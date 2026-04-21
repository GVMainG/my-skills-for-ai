from __future__ import annotations

import sys
from datetime import datetime

from ..analyzers.keyword_extractor import extract_keywords
from ..analyzers.semantic_analyzer import SemanticAnalyzer
from ..core.config import Config
from ..core.note import Note, SearchResult
from ..core.vault import VaultManager, VaultNotFoundError

_SEP = "━" * 51
_STARS = {(0.8, 1.0): "⭐⭐⭐", (0.5, 0.8): "⭐⭐", (0.0, 0.5): "⭐"}


def _stars(score: float) -> str:
    for (lo, hi), label in _STARS.items():
        if lo <= score <= hi:
            return label
    return "⭐"


def _preview(content: str, keywords: list[str], length: int = 120) -> str:
    lower = content.lower()
    for kw in keywords:
        idx = lower.find(kw.lower())
        if idx != -1:
            start = max(0, idx - 30)
            end = min(len(content), idx + length)
            snippet = content[start:end].replace("\n", " ").strip()
            return snippet[:length] + ("..." if len(snippet) > length else "")
    return content[:length].replace("\n", " ").strip() + "..."


def _level1_tags(query: str, vault: VaultManager, analyzer: SemanticAnalyzer) -> list[Note]:
    keywords = extract_keywords(query, top_n=8)
    mapped = analyzer.map_keywords_to_tags(keywords, threshold=0.2)
    candidates_set: set = set()
    candidates: list[Note] = []
    for tag, _ in mapped:
        for note in vault.get_notes_by_tag(tag):
            if note.path not in candidates_set:
                candidates_set.add(note.path)
                candidates.append(note)
    return candidates


def _level2_keywords(
    query: str, candidates: list[Note], threshold: float, all_notes: list[Note]
) -> list[tuple[Note, float, list[str]]]:
    keywords = extract_keywords(query, top_n=10)
    pool = candidates if candidates else all_notes
    scored: list[tuple[Note, float, list[str]]] = []
    for note in pool:
        lower = note.content.lower()
        count = 0
        matched_kws = []
        for kw in keywords:
            c = lower.count(kw.lower())
            if c:
                count += c
                matched_kws.append(kw)
        if not count:
            continue
        length_factor = max(1, len(note.content) / 1000)
        norm = count / length_factor
        if norm > threshold:
            scored.append((note, norm, matched_kws))
    return sorted(scored, key=lambda x: x[1], reverse=True)


def _level3_backlinks(
    top_results: list[tuple[Note, float, list[str]]],
    vault: VaultManager,
    max_expand: int = 5,
) -> list[tuple[Note, float, list[str]]]:
    related: list[tuple[Note, float, list[str]]] = []
    seen = {t[0].path for t in top_results}
    for note, score, kws in top_results[:max_expand]:
        for bl in vault.find_backlinks(note):
            if bl.path not in seen:
                seen.add(bl.path)
                related.append((bl, score * 0.5, kws))
    return related


def _prioritize(
    results: list[tuple[Note, float, list[str]]],
    vault: VaultManager,
    backlinks_index: dict,
) -> list[tuple[Note, float, list[str]]]:
    def priority(item: tuple[Note, float, list[str]]) -> float:
        note, base, _ = item
        bl_count = len(backlinks_index.get(note.path, []))
        recency = 0.0
        if note.modified:
            days = (datetime.now() - note.modified).days
            recency = max(0, 1 - days / 365)
        return base + bl_count * 0.5 + recency * 0.3

    return sorted(results, key=priority, reverse=True)


def run_search(
    query: str,
    config: Config,
    max_results: int | None = None,
    include_backlinks: bool = True,
    scope: str | None = None,
    tag_filter: list[str] | None = None,
) -> None:
    try:
        vault = VaultManager(config)
    except VaultNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    analyzer = SemanticAnalyzer(vault.tags_manager)
    limit = max_results or config.limits.search_max_results
    threshold = config.search.relevance_threshold

    all_notes = vault.get_all_notes()
    if scope:
        from pathlib import Path as _Path
        scope_path = str(_Path(scope))
        all_notes = [n for n in all_notes if str(n.path).startswith(scope_path)]
    if tag_filter:
        all_notes = [n for n in all_notes if any(t in n.tags for t in tag_filter)]

    backlinks_index = vault.build_backlinks_index()

    candidates = _level1_tags(query, vault, analyzer)
    scored = _level2_keywords(query, candidates, threshold, all_notes)

    if include_backlinks and config.search.enable_backlink_expansion:
        related = _level3_backlinks(scored, vault)
        combined = scored + related
    else:
        combined = scored

    prioritized = _prioritize(combined, vault, backlinks_index)

    seen: set = set()
    final: list[tuple[Note, float, list[str]]] = []
    for item in prioritized:
        if item[0].path not in seen:
            seen.add(item[0].path)
            final.append(item)

    if final:
        max_score = max(s for _, s, _ in final)
        if max_score > 0:
            final = [(n, s / max_score, kw) for n, s, kw in final]

    print(f"\n🔍 Search: \"{query}\"\n")
    print(f"Найдено {min(len(final), limit)} результатов (просмотрено {len(all_notes)} заметок):\n")
    print(_SEP)

    main_results = final[:limit]
    backlink_extras = [item for item in final[limit:limit + 5]]

    for idx, (note, score, kws) in enumerate(main_results, start=1):
        try:
            rel_path = note.path.relative_to(vault.root)
        except ValueError:
            rel_path = note.path
        stars = _stars(score)
        bl_count = len(backlinks_index.get(note.path, []))
        date_str = note.modified.strftime("%Y-%m-%d") if note.modified else "?"
        preview = _preview(note.content, kws)
        tags_str = ", ".join(note.tags[:4]) if note.tags else "—"

        print(f"\n{idx}. {note.path.stem} (релевантность: {score:.2f}) {stars}")
        print(f"   Путь: {rel_path}")
        print(f"   Теги: {tags_str}")
        print(f"   Изменено: {date_str}")
        print(f"   Обзор: {preview}")
        if bl_count:
            print(f"   Бэклинки: {bl_count} заметок")

    if backlink_extras and main_results:
        print(f"\n{_SEP}\nСвязанные заметки (через бэклинки):")
        for note, score, kws in backlink_extras[:3]:
            print(f"  - {note.path.stem}")
