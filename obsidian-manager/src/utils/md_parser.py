from __future__ import annotations

import re
from typing import Any

import yaml


def parse_frontmatter(raw_content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return (frontmatter_dict, body_content)."""
    if not raw_content.startswith("---"):
        return {}, raw_content

    end = raw_content.find("---", 3)
    if end == -1:
        return {}, raw_content

    yaml_block = raw_content[3:end].strip()
    body = raw_content[end + 3:].lstrip("\n")

    try:
        data = yaml.safe_load(yaml_block) or {}
    except yaml.YAMLError:
        data = _try_fix_yaml(yaml_block)

    return data if isinstance(data, dict) else {}, body


def _try_fix_yaml(yaml_str: str) -> dict[str, Any]:
    """Attempt to recover common YAML frontmatter errors."""
    lines = yaml_str.splitlines()
    fixed_lines = []
    for line in lines:
        # Quote unquoted values containing special chars
        if ":" in line:
            key, _, val = line.partition(":")
            val = val.strip()
            if val and not val.startswith(("[", "{", '"', "'")):
                val = f'"{val}"'
            fixed_lines.append(f"{key}: {val}")
        else:
            fixed_lines.append(line)
    try:
        return yaml.safe_load("\n".join(fixed_lines)) or {}
    except yaml.YAMLError:
        return {}


def extract_tags_from_frontmatter(frontmatter: dict[str, Any]) -> list[str]:
    """Extract tags list from frontmatter, normalising to '#category/sub' form."""
    raw = frontmatter.get("tags", [])
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",")]
    if not isinstance(raw, list):
        return []
    return [_normalise_tag(str(t)) for t in raw if t]


def extract_inline_tags(content: str) -> list[str]:
    """Extract #tag/sub tags written inline in the note body."""
    return re.findall(r'(?<!\[)#([\w/а-яёА-ЯЁ][\w/а-яёА-ЯЁ\-]*)', content)


def _normalise_tag(tag: str) -> str:
    tag = tag.strip().lstrip("#")
    return f"#{tag}"


def build_frontmatter_block(data: dict[str, Any]) -> str:
    """Serialise a dict into a YAML frontmatter block."""
    return "---\n" + yaml.dump(data, allow_unicode=True, default_flow_style=False) + "---\n"


def inject_frontmatter(raw_content: str, new_fm: dict[str, Any]) -> str:
    """Replace or prepend frontmatter in a raw markdown string."""
    _, body = parse_frontmatter(raw_content)
    return build_frontmatter_block(new_fm) + "\n" + body


def find_line_number(content: str, target: str) -> int:
    """Return 1-based line number of first occurrence of target in content."""
    for i, line in enumerate(content.splitlines(), start=1):
        if target in line:
            return i
    return 0
