from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Note:
    path: Path
    filename: str
    content: str
    raw_content: str
    frontmatter: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    backlinks: list[str] = field(default_factory=list)
    created: datetime | None = None
    modified: datetime | None = None
    word_count: int = 0

    def __post_init__(self) -> None:
        self.word_count = len(self.content.split())
        self.links = self._extract_links()

    def _extract_links(self) -> list[str]:
        # Match [[filename]] or [[filename|alias]] or [[filename#heading]]
        # Allow # inside filename (e.g. C#), but stop at | or ]]
        raw = re.findall(r'\[\[([^\]]+)\]\]', self.content)
        links = []
        for r in raw:
            # Strip alias (after |) and heading anchor (last # if followed by non-space text)
            name = r.split("|")[0]
            # Only strip heading anchors: '#heading' not '#' in tech names like 'C#'
            # Heuristic: if # is not at end and followed by uppercase/space, treat as heading
            anchor_match = re.search(r'\s#\S+$|#[A-Z][a-z]', name)
            if anchor_match:
                name = name[:anchor_match.start()]
            links.append(name.strip())
        return links

    def has_frontmatter(self) -> bool:
        return bool(self.frontmatter)

    @property
    def folder(self) -> str:
        return str(self.path.parent)

    @property
    def stem(self) -> str:
        return self.path.stem

    def __hash__(self) -> int:
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Note):
            return False
        return self.path == other.path


@dataclass
class TagRecommendation:
    tag: str
    reason: str
    confidence: float


@dataclass
class TagAnalysisResult:
    note_path: Path
    current_tags: list[str]
    add: list[TagRecommendation] = field(default_factory=list)
    remove: list[TagRecommendation] = field(default_factory=list)
    new_tags: list[TagRecommendation] = field(default_factory=list)


@dataclass
class AuditIssue:
    issue_type: str
    severity: str  # high | medium | low
    file_path: str
    description: str
    auto_fix: bool = False
    fix_action: str = ""
    suggestion: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    note: Note
    score: float
    matched_keywords: list[str] = field(default_factory=list)
    via_backlink: bool = False
