from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TagNode:
    tag: str           # e.g. "#it/csharp"
    parent: str | None = None
    description: str = ""
    children: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


class TagsManager:
    """Parses and manages the TAGS_HIERARCHICAL.md tag hierarchy."""

    def __init__(self) -> None:
        self.tags: dict[str, TagNode] = {}

    def load_from_file(self, path: Path) -> None:
        if not path.exists():
            return
        content = path.read_text(encoding="utf-8")
        self._parse(content)

    def _parse(self, content: str) -> None:
        """Parse tag hierarchy from markdown.

        Supports two formats:
        1. Classic list:
           ## #category
           - #category/sub — описание

        2. Table format with heading:
           ### N. CATEGORY ( #category )
           | #category/sub  | описание |
        """
        current_parent: str | None = None
        for line in content.splitlines():
            stripped = line.strip()

            # Top-level heading — extract tag from heading text
            # Handles: "## #tag", "### N. TITLE ( #tag )", "## #tag — desc"
            h_match = re.match(r'^#{1,4}\s+(?:.*?\(\s*)?(#[\w/а-яёА-ЯЁ\-]+)', stripped)
            if h_match:
                tag = h_match.group(1)
                # Only treat as category if it's a short top-level tag (no /)
                if "/" not in tag or tag.count("/") == 0:
                    current_parent = tag
                    if tag not in self.tags:
                        self.tags[tag] = TagNode(tag=tag)
                continue

            # List item: "- #tag — description" or "*  #tag  description"
            item = re.match(r'^[-*]\s+#?([\w/а-яёА-ЯЁ\-]+)\s*(?:[-—]\s*(.*))?$', stripped)
            if item and "/" in item.group(1):
                raw_tag = item.group(1)
                tag = f"#{raw_tag}" if not raw_tag.startswith("#") else raw_tag
                description = (item.group(2) or "").strip()
                self._add_child_tag(tag, current_parent, description)
                continue

            # Table row: | #tag | description | or |  #tag  | desc |
            table_row = re.match(r'^\|\s*(#[\w/а-яёА-ЯЁ\-]+)\s*\|\s*(.*?)\s*\|?$', stripped)
            if table_row:
                tag = table_row.group(1).strip()
                description = table_row.group(2).strip()
                if "/" in tag:  # Only child tags
                    self._add_child_tag(tag, current_parent, description)

    def _add_child_tag(self, tag: str, parent: str | None, description: str) -> None:
        keywords = self._extract_keywords_from_description(description)
        node = TagNode(
            tag=tag,
            parent=parent,
            description=description,
            keywords=keywords,
        )
        self.tags[tag] = node
        if parent and parent in self.tags:
            self.tags[parent].children.append(tag)

    def _extract_keywords_from_description(self, description: str) -> list[str]:
        """Extract relevant keywords from a tag description string."""
        words = re.findall(r'[\w а-яёА-ЯЁ]+', description.lower())
        return [w.strip() for w in words if len(w.strip()) > 2]

    @property
    def all_tags(self) -> set[str]:
        return set(self.tags.keys())

    def find_closest_tag(self, tag: str) -> str | None:
        """Find the most similar valid tag using character overlap."""
        tag_clean = tag.lstrip("#").lower()
        best, best_score = None, 0.0
        for valid in self.tags:
            valid_clean = valid.lstrip("#").lower()
            common = sum(1 for c in tag_clean if c in valid_clean)
            score = common / max(len(tag_clean), len(valid_clean), 1)
            if score > best_score:
                best_score = score
                best = valid
        return best

    def get_keywords_for_tag(self, tag: str) -> list[str]:
        node = self.tags.get(tag)
        if not node:
            return []
        # Include tag parts as keywords
        parts = tag.lstrip("#").replace("/", " ").split()
        return list(set(node.keywords + parts))

    def create_default(self, path: Path) -> None:
        """Create a minimal TAGS_HIERARCHICAL.md if none exists."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = """\
# Иерархия тегов

## #it
- #it/csharp — C# и .NET разработка
- #it/python — Python разработка
- #it/docker — Docker и контейнеризация
- #it/архитектура — Архитектурные паттерны, SOLID
- #it/многопоточность — Async/await, threading, concurrency

## #инфраструктура
- #инфраструктура/homelab — Домашний сервер и self-hosted
- #инфраструктура/linux — Linux системное администрирование
- #инфраструктура/развертывание — CI/CD, deployment
- #инфраструктура/проксирование — Reverse proxy, tunneling

## #личное
- #личное/дневник — Дневниковые записи
- #личное/рефлексия — Рефлексия и самоанализ
- #личное/цели — Цели и планы

## #карьера
- #карьера/достижения — Профессиональные достижения
- #карьера/собеседования — Подготовка к собеседованиям
- #карьера/обучение — Учебные материалы

## #творчество
- #творчество/поэзия — Стихи и поэзия
- #творчество/видео — Видеоконтент

## #входящие
- #входящие/необработанное — Необработанные заметки

## #архив
- #архив/устаревшее — Устаревшие материалы
"""
        path.write_text(content, encoding="utf-8")
        self._parse(content)
