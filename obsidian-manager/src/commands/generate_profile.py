from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from ..analyzers.graph_builder import NoteGraph
from ..analyzers.keyword_extractor import extract_keywords
from ..analyzers.semantic_analyzer import SemanticAnalyzer
from ..core.config import Config
from ..core.vault import VaultManager, VaultNotFoundError

_SEP = "━" * 51

_LEVEL_LABEL = {
    "expert": "Экспертный уровень (10+ упоминаний)",
    "intermediate": "Промежуточный уровень (5–9 упоминаний)",
    "familiar": "Знакомство (2–4 упоминания)",
    "beginner": "Начальный уровень (1 упоминание)",
}

_TRAIT_RU = {
    "introversion": "Интроверсия",
    "extraversion": "Экстраверсия",
    "conscientiousness": "Добросовестность",
    "openness": "Открытость опыту",
    "neuroticism": "Нейротизм",
}

_COGNITIVE_RU = {
    "systematic": "Системное",
    "intuitive": "Интуитивное",
    "analytical": "Аналитическое",
    "holistic": "Холистическое",
}


def _build_graph(notes: list, vault: VaultManager) -> NoteGraph:
    graph = NoteGraph()
    for note in notes:
        graph.add_node(note.filename, tags=note.tags, word_count=note.word_count)
    for note in notes:
        for link_name in note.links:
            target = vault.resolve_link(link_name)
            if target:
                graph.add_edge(note.filename, target.name)
    return graph


def _format_skills_section(skills: dict) -> str:
    by_level: dict[str, list] = {lv: [] for lv in _LEVEL_LABEL}
    for entry in skills.values():
        by_level.setdefault(entry.level, []).append(entry)

    lines = ["## 2. Технические навыки\n"]
    for level_key, label in _LEVEL_LABEL.items():
        entries = by_level.get(level_key, [])
        if not entries:
            continue
        lines.append(f"### {label}\n")
        for entry in sorted(entries, key=lambda e: e.mentions, reverse=True):
            lines.append(f"**{entry.technology}**")
            lines.append(f"- Упоминаний: {entry.mentions}")
            if entry.quotes:
                lines.append(f"- Цитата: _{entry.quotes[0]}_")
            lines.append("")
    return "\n".join(lines)


def _format_portrait_section(portrait) -> str:
    lines = ["## 4. Психологический портрет\n"]

    # Cognitive style
    cs = portrait.cognitive_style
    dominant_ru = _COGNITIVE_RU.get(cs.dominant, cs.dominant)
    lines.append("### 4.1. Когнитивный стиль\n")
    lines.append(f"**Доминирующий стиль:** {dominant_ru} мышление\n")
    for style, pct in sorted(cs.distribution.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {_COGNITIVE_RU.get(style, style)}: {pct:.1f}%")
    lines.append("")

    # Personality
    pt = portrait.personality_traits
    lines.append("### 4.2. Черты характера (Big Five)\n")
    lines.append("**Топ черты:**")
    for i, trait in enumerate(pt.top_traits[:3], 1):
        score = pt.scores.get(trait, 0)
        lines.append(f"{i}. **{_TRAIT_RU.get(trait, trait)}** — упоминаний индикаторов: {score}")
    lines.append("")

    # Values
    if portrait.values:
        lines.append("### 4.3. Ценности\n")
        for i, val in enumerate(portrait.values[:5], 1):
            lines.append(f"{i}. **{val.capitalize()}**")
        lines.append("")

    # Behavioral patterns
    if portrait.behavioral_patterns:
        lines.append("### 4.4. Паттерны поведения\n")
        for key, desc in portrait.behavioral_patterns.items():
            lines.append(f"**{key.replace('_', ' ').capitalize()}:** {desc}")
        lines.append("")

    # Contradictions
    if portrait.contradictions:
        lines.append("### 4.5. Противоречия и эволюция взглядов\n")
        lines.append("⚠️ **Обнаружены противоречия в заметках:**\n")
        for c in portrait.contradictions[:3]:
            lines.append(f"**Тема: {c.topic}**")
            lines.append(f"- _{c.statement1[:150]}_")
            lines.append(f"- _{c.statement2[:150]}_")
            if c.time_gap_days:
                lines.append(f"- Разрыв: {c.time_gap_days} дней")
            lines.append("")

    return "\n".join(lines)


def _format_knowledge_map(graph: NoteGraph, notes: list) -> str:
    stats = graph.stats
    hubs = graph.find_hubs(5)
    clusters = graph.detect_clusters_simple()

    lines = ["## 7. Карта знаний\n"]
    lines.append(f"**Статистика графа:**")
    lines.append(f"- Всего заметок: {stats['total_notes']}")
    lines.append(f"- Всего связей: {stats['total_edges']}")
    if stats["total_notes"] > 0:
        avg = stats["total_edges"] / stats["total_notes"]
        lines.append(f"- Средняя связность: {avg:.2f} связей на заметку")
    lines.append("")

    if hubs:
        lines.append("**Hub-заметки (наибольшее число бэклинков):**")
        for i, (name, count) in enumerate(hubs, 1):
            lines.append(f"{i}. {name} ({count} бэклинков)")
        lines.append("")

    if clusters:
        lines.append("**Кластеры знаний:**\n")
        for cluster_name, note_names in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            lines.append(f"**Кластер: {cluster_name} ({len(note_names)} заметок)**")
        lines.append("")

    return "\n".join(lines)


def _format_interests(notes: list) -> str:
    tag_counter: Counter = Counter()
    for note in notes:
        for tag in note.tags:
            top = tag.lstrip("#").split("/")[0]
            tag_counter[top] += 1

    lines = ["## 3. Интересы и увлечения\n"]
    lines.append("**Топ тем по количеству заметок:**")
    for i, (topic, count) in enumerate(tag_counter.most_common(8), 1):
        lines.append(f"{i}. {topic.capitalize()} ({count} заметок)")
    lines.append("")
    return "\n".join(lines)


def _format_current_context(notes: list, config: Config) -> str:
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=30)
    recent = [n for n in notes if n.modified and n.modified >= cutoff]
    recent.sort(key=lambda n: n.modified or datetime.min, reverse=True)

    lines = ["## 6. Текущий контекст\n"]
    lines.append("### 6.1. Активные темы (последние 30 дней)\n")

    if recent:
        kws = extract_keywords(" ".join(n.content for n in recent[:20]), top_n=10)
        for i, kw in enumerate(kws[:5], 1):
            count = sum(1 for n in recent if kw.lower() in n.content.lower())
            lines.append(f"{i}. **{kw.capitalize()}** — {count} заметок")
    else:
        lines.append("_Нет недавних заметок._")

    lines.append("")
    return "\n".join(lines)


def generate_profile(
    config: Config,
    update: bool = False,
    output_path: str | None = None,
    sections: list[str] | None = None,
) -> None:
    try:
        vault = VaultManager(config)
    except VaultNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    output = Path(output_path) if output_path else vault.root / config.profile.output_file

    if output.exists() and not update:
        print(f"⚠️ Профиль уже существует: {output}")
        print("Используйте --update для обновления.")
        sys.exit(0)

    active_sections = sections or config.profile.sections
    depth = config.profile.analysis.depth

    print(f"\n🔄 Генерация профиля (глубина: {depth})...\n")

    # Load notes (exclude configured folders/tags)
    exclude_folders = config.profile.sources.exclude_folders
    all_notes = vault.get_all_notes(exclude_folders=exclude_folders)
    print(f"  Загружено заметок: {len(all_notes)}")

    analyzer = SemanticAnalyzer(vault.tags_manager)

    print("  Извлечение технических навыков...")
    skills = analyzer.extract_technical_skills(all_notes)

    portrait = None
    if depth == "deep" and "psychological_portrait" in active_sections:
        print("  Построение психологического портрета...")
        personal_notes = vault.get_notes_by_tags(["#личное/дневник", "#личное/рефлексия"])
        portrait = analyzer.build_psychological_portrait(personal_notes or all_notes[:30])

    print("  Построение графа знаний...")
    graph = _build_graph(all_notes, vault)

    # Generate profile markdown
    now = datetime.now()
    frontmatter = (
        f"---\n"
        f"generated: {now.isoformat()}\n"
        f"last_updated: {now.isoformat()}\n"
        f"version: 1.0\n"
        f"sources_analyzed: {len(all_notes)}\n"
        f"analysis_depth: {depth}\n"
        f"---\n"
    )

    header = (
        "\n# Профиль пользователя\n\n"
        "> Этот файл автоматически генерируется на основе анализа всех заметок в vault.\n"
        f"> Последнее обновление: {now.strftime('%d %B %Y')}\n\n"
        f"---\n\n"
    )

    parts = [frontmatter, header]

    if "basic_info" in active_sections:
        parts.append("## 1. Базовая информация\n\n_[Информация извлекается из заметок с тегами #карьера]_\n\n---\n\n")

    if "technical_skills" in active_sections:
        parts.append(_format_skills_section(skills))
        parts.append("\n---\n\n")

    if "interests" in active_sections:
        parts.append(_format_interests(all_notes))
        parts.append("\n---\n\n")

    if "psychological_portrait" in active_sections and portrait:
        parts.append(_format_portrait_section(portrait))
        parts.append("\n---\n\n")

    if "current_context" in active_sections:
        parts.append(_format_current_context(all_notes, config))
        parts.append("\n---\n\n")

    if "knowledge_map" in active_sections:
        parts.append(_format_knowledge_map(graph, all_notes))
        parts.append("\n---\n\n")

    if "metadata" in active_sections:
        parts.append("## 8. Метаданные для AI\n\n")
        parts.append("### 8.1. Стиль общения\n\n")
        parts.append("- Обращаться формально, на «вы»\n")
        parts.append("- Давать структурированные ответы (заголовки, списки)\n")
        parts.append("- Избегать вводных фраз и «воды»\n")
        parts.append("- Не смягчать критику — прямота ценится\n\n")
        parts.append("---\n\n")

    if "changelog" in active_sections:
        parts.append(f"## 9. История изменений\n\n### v1.0 ({now.strftime('%Y-%m-%d')})\n\n")
        parts.append(f"**Создан {'обновлён' if update else 'начальный'} профиль**\n")
        parts.append(f"- Проанализировано: {len(all_notes)} заметок\n")
        parts.append(f"- Глубина анализа: {depth}\n\n")
        parts.append("---\n\n")
        parts.append("*Этот профиль — живой документ. Обновляется автоматически раз в месяц.*\n\n")
        parts.append(f"*Для ручного обновления: `notes-manager generate-profile --update`*\n")

    output.write_text("".join(parts), encoding="utf-8")

    print(f"\n{_SEP}")
    print(f"✅ Профиль {'обновлён' if update else 'создан'}: {output}")
    print(f"   Заметок проанализировано: {len(all_notes)}")
    print(f"   Технологий обнаружено: {len(skills)}")
    if portrait:
        print(f"   Когнитивный стиль: {portrait.cognitive_style.dominant}")
        print(f"   Противоречий найдено: {len(portrait.contradictions)}")
    graph_stats = graph.stats
    print(f"   Граф: {graph_stats['total_notes']} узлов, {graph_stats['total_edges']} рёбер")
