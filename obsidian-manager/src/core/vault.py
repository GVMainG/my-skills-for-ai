from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from ..core.config import Config
from ..core.note import Note
from ..core.tags import TagsManager
from ..utils.md_parser import (
    extract_inline_tags,
    extract_tags_from_frontmatter,
    parse_frontmatter,
)

logger = logging.getLogger("notes-manager.vault")

SKIP_DIRS = {".git", ".obsidian", ".trash"}


class VaultNotFoundError(Exception):
    pass


class VaultManager:
    def __init__(self, config: Config) -> None:
        if config.vault_path is None or not config.vault_path.exists():
            raise VaultNotFoundError(
                f"Vault не найден: {config.vault_path}"
            )
        self.root = config.vault_path
        self.config = config
        self.tags_manager = TagsManager()
        self._notes_cache: dict[Path, Note] | None = None
        self._backlinks_cache: dict[Path, list[Path]] | None = None

        tags_path = config.tags_file
        if tags_path and tags_path.exists():
            self.tags_manager.load_from_file(tags_path)
        elif tags_path:
            logger.warning("Файл тегов не найден: %s", tags_path)

    # ------------------------------------------------------------------
    # Note loading
    # ------------------------------------------------------------------

    def _load_note(self, path: Path) -> Note | None:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Не удалось прочитать %s: %s", path, e)
            return None

        frontmatter, body = parse_frontmatter(raw)

        fm_tags = extract_tags_from_frontmatter(frontmatter)
        inline_tags = [f"#{t}" for t in extract_inline_tags(body)]
        all_tags = list(dict.fromkeys(fm_tags + inline_tags))

        stat = path.stat()
        modified = datetime.fromtimestamp(stat.st_mtime)
        created_raw = frontmatter.get("created")
        if isinstance(created_raw, str):
            try:
                created = datetime.fromisoformat(created_raw)
            except ValueError:
                created = modified
        elif isinstance(created_raw, datetime):
            created = created_raw
        else:
            created = datetime.fromtimestamp(stat.st_ctime)

        return Note(
            path=path,
            filename=path.name,
            content=body,
            raw_content=raw,
            frontmatter=frontmatter,
            tags=all_tags,
            created=created,
            modified=modified,
        )

    def get_all_notes(self, exclude_folders: list[str] | None = None) -> list[Note]:
        exclude = set(exclude_folders or [])
        exclude |= SKIP_DIRS
        notes: list[Note] = []
        for md_path in self.root.rglob("*.md"):
            # Skip excluded folders
            rel_parts = md_path.relative_to(self.root).parts
            if any(part in exclude for part in rel_parts):
                continue
            note = self._load_note(md_path)
            if note:
                notes.append(note)
        return notes

    def get_notes_in_folder(self, folder: str) -> list[Note]:
        folder_path = self.root / folder
        if not folder_path.exists():
            return []
        notes = []
        for md_path in folder_path.rglob("*.md"):
            note = self._load_note(md_path)
            if note:
                notes.append(note)
        return notes

    def get_notes_by_tag(self, tag: str) -> list[Note]:
        """Return notes that have the given tag (supports wildcard '#it/*')."""
        notes = self.get_all_notes()
        if tag.endswith("/*"):
            prefix = tag[:-2]
            return [n for n in notes if any(t.startswith(prefix) for t in n.tags)]
        return [n for n in notes if tag in n.tags]

    def get_notes_by_tags(self, tags: list[str]) -> list[Note]:
        """Return notes matching any of the provided tags (supports wildcards)."""
        result_set: set[Path] = set()
        result_list: list[Note] = []
        for tag in tags:
            for note in self.get_notes_by_tag(tag):
                if note.path not in result_set:
                    result_set.add(note.path)
                    result_list.append(note)
        return result_list

    def get_note(self, name: str) -> Note | None:
        """Find a note by filename (without extension) or full path."""
        for md_path in self.root.rglob("*.md"):
            if md_path.stem == name or md_path.name == name:
                return self._load_note(md_path)
        return None

    def get_recent_notes(self, days: int = 7, tags: list[str] | None = None) -> list[Note]:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        all_notes = self.get_all_notes()
        recent = [n for n in all_notes if n.modified and n.modified >= cutoff]
        if tags:
            recent = [n for n in recent if any(
                any(t.startswith(tag.rstrip("*")) for t in n.tags) for tag in tags
            )]
        return sorted(recent, key=lambda n: n.modified or datetime.min, reverse=True)

    # ------------------------------------------------------------------
    # Link / backlink resolution
    # ------------------------------------------------------------------

    def resolve_link(self, link: str) -> Path | None:
        """Resolve an Obsidian wikilink to an absolute path."""
        link_clean = link.split("|")[0].split("#")[0].strip()
        for md_path in self.root.rglob("*.md"):
            if md_path.stem == link_clean or md_path.name == link_clean:
                return md_path
        return None

    def find_backlinks(self, note: Note) -> list[Note]:
        """Return all notes that contain a [[link]] pointing to the given note."""
        result = []
        target_names = {note.path.stem, note.path.name}
        for md_path in self.root.rglob("*.md"):
            if md_path == note.path:
                continue
            n = self._load_note(md_path)
            if n and any(link in target_names for link in n.links):
                result.append(n)
        return result

    def build_backlinks_index(self) -> dict[Path, list[Path]]:
        """Pre-build a full backlinks index for the entire vault."""
        if self._backlinks_cache is not None:
            return self._backlinks_cache
        index: dict[Path, list[Path]] = {}
        all_notes = self.get_all_notes()
        for note in all_notes:
            for link_name in note.links:
                target = self.resolve_link(link_name)
                if target:
                    index.setdefault(target, []).append(note.path)
        self._backlinks_cache = index
        return index

    # ------------------------------------------------------------------
    # Folder helpers
    # ------------------------------------------------------------------

    @property
    def folder_paths(self) -> dict[str, Path]:
        f = self.config.folders
        return {
            "inbox": self.root / f.inbox,
            "daily": self.root / f.daily,
            "areas": self.root / f.areas,
            "projects": self.root / f.projects,
            "archive": self.root / f.archive,
            "service": self.root / f.service,
        }
