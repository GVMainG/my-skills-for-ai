from __future__ import annotations

import sys
from pathlib import Path

from ..analyzers.keyword_extractor import extract_keywords
from ..analyzers.semantic_analyzer import SemanticAnalyzer
from ..core.config import Config
from ..core.note import Note, TagAnalysisResult, TagRecommendation
from ..core.vault import VaultManager, VaultNotFoundError
from ..utils.md_parser import inject_frontmatter, parse_frontmatter


def _load_note_from_path(filepath: Path) -> Note:
    raw = filepath.read_text(encoding="utf-8", errors="replace")
    from ..utils.md_parser import (
        extract_inline_tags,
        extract_tags_from_frontmatter,
    )
    from datetime import datetime

    frontmatter, body = parse_frontmatter(raw)
    fm_tags = extract_tags_from_frontmatter(frontmatter)
    inline_tags = [f"#{t}" for t in extract_inline_tags(body)]
    all_tags = list(dict.fromkeys(fm_tags + inline_tags))
    stat = filepath.stat()
    return Note(
        path=filepath,
        filename=filepath.name,
        content=body,
        raw_content=raw,
        frontmatter=frontmatter,
        tags=all_tags,
        modified=datetime.fromtimestamp(stat.st_mtime),
    )


def analyze_tags(
    filepath: str,
    config: Config,
    auto_apply: bool = False,
    dry_run: bool = False,
) -> None:
    path = Path(filepath)
    if not path.exists():
        print(f"❌ Файл не найден: {filepath}")
        sys.exit(1)
    if path.suffix.lower() != ".md":
        print("❌ Файл должен быть .md")
        sys.exit(1)

    # Load vault for tag hierarchy
    try:
        vault = VaultManager(config)
    except VaultNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    analyzer = SemanticAnalyzer(vault.tags_manager)
    note = _load_note_from_path(path)

    print(f"\n📝 Анализ тегов: {filepath}\n")

    print(f"Текущие теги ({len(note.tags)}):")
    for tag in note.tags:
        print(f"  {tag}")

    # Extract keywords and map to tags
    keywords = extract_keywords(note.content, top_n=15)
    mapped = analyzer.map_keywords_to_tags(keywords, threshold=0.25)
    recommended_tags = {tag for tag, _ in mapped}

    current_set = set(note.tags)

    # Determine add/remove/new
    to_add: list[TagRecommendation] = []
    to_remove: list[TagRecommendation] = []
    new_suggestions: list[TagRecommendation] = []

    valid_tags = vault.tags_manager.all_tags

    for tag, score in mapped:
        if tag not in current_set:
            reason = f"Ключевые слова: {', '.join(keywords[:5])}"
            to_add.append(TagRecommendation(tag=tag, reason=reason, confidence=score))

    for tag in note.tags:
        if tag not in valid_tags:
            new_suggestions.append(TagRecommendation(
                tag=tag,
                reason="Тег отсутствует в иерархии",
                confidence=0.0,
            ))
        elif tag not in recommended_tags:
            overlap = sum(1 for kw in keywords if kw.lower() in tag.lower())
            if overlap == 0:
                to_remove.append(TagRecommendation(
                    tag=tag,
                    reason="Содержимое не подтверждает тег",
                    confidence=0.8,
                ))

    # Respect 1-5 tags limit
    final_count = len(current_set) - len(to_remove) + len(to_add)

    print("\nРекомендации:\n")

    if to_remove:
        print("❌ Удалить:")
        for rec in to_remove:
            print(f"  {rec.tag}")
            print(f"  Причина: {rec.reason}")
        print()

    if to_add:
        print("✅ Добавить:")
        for rec in to_add:
            print(f"  {rec.tag}")
            kws = ", ".join(f'"{k}"' for k in keywords[:4])
            print(f"  Причина: Ключевые слова — {kws}")
        print()

    if new_suggestions:
        print("⚠️ Теги не в иерархии:")
        for rec in new_suggestions:
            print(f"  {rec.tag}")
            closest = vault.tags_manager.find_closest_tag(rec.tag)
            if closest:
                print(f"  💡 Похожий тег: {closest}")
            print(f"  Рекомендация: Добавить в TAGS_HIERARCHICAL.md или заменить")
        print()

    print(f"Итого тегов после применения: {final_count} ({'в пределах нормы 1–5' if 1 <= final_count <= 5 else '⚠️ вне нормы 1–5'})")

    if dry_run:
        print("\n[dry-run] Изменения не применены.")
        return

    if not to_add and not to_remove:
        print("\n✅ Теги в порядке. Изменений не требуется.")
        return

    if auto_apply:
        _apply_changes(path, note, to_add, to_remove)
    else:
        answer = input("\nПрименить изменения? [Y/n] ").strip().lower()
        if answer in ("y", ""):
            _apply_changes(path, note, to_add, to_remove)
        else:
            print("Отмена.")


def _apply_changes(
    path: Path,
    note: Note,
    to_add: list[TagRecommendation],
    to_remove: list[TagRecommendation],
) -> None:
    remove_set = {r.tag for r in to_remove}
    add_list = [r.tag for r in to_add]

    new_tags = [t for t in note.tags if t not in remove_set]
    for tag in add_list:
        if tag not in new_tags:
            new_tags.append(tag)

    new_fm = dict(note.frontmatter)
    # Store tags without leading #
    new_fm["tags"] = [t.lstrip("#") for t in new_tags]

    new_content = inject_frontmatter(note.raw_content, new_fm)
    path.write_text(new_content, encoding="utf-8")
    print("✅ Теги обновлены.")
