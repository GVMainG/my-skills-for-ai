from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def validate_vault_path(path: str | Path) -> tuple[bool, str]:
    """Check that path exists and looks like an Obsidian vault."""
    p = Path(path)
    if not p.exists():
        return False, f"Путь не существует: {path}"
    if not p.is_dir():
        return False, f"Путь не является директорией: {path}"
    md_files = list(p.rglob("*.md"))
    if not md_files:
        return False, "В директории не найдено .md файлов"
    return True, "OK"


def validate_tag_format(tag: str) -> bool:
    """Validate #category/subcategory tag format (1-2 levels)."""
    # Allow leading # or not
    tag = tag.lstrip("#")
    return bool(re.match(r'^[\w а-яёА-ЯЁ][\w а-яёА-ЯЁ\-]*(\/[\w а-яёА-ЯЁ][\w а-яёА-ЯЁ\-]*)?$', tag))


def validate_note_structure(frontmatter: dict[str, Any], content: str, min_length: int = 100) -> list[str]:
    """Return list of structural issues found in a note."""
    issues = []
    if not frontmatter:
        issues.append("missing_frontmatter")
    if len(content.strip()) < min_length:
        issues.append("too_short")
    return issues
