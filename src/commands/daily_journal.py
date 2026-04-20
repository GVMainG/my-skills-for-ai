from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

from ..analyzers.keyword_extractor import extract_keywords, extract_main_topics
from ..core.config import Config
from ..core.note import Note
from ..core.vault import VaultManager, VaultNotFoundError

_SEP = "━" * 51

_BASE_QUESTIONS = [
    "Что сегодня было самым важным?",
    "Чему новому научился?",
    "Какие эмоции испытывал?",
    "Что хотел бы изменить в сегодняшнем дне?",
    "О чём думал больше всего?",
    "Что завтра хочется сделать иначе?",
    "Какой небольшой прогресс был замечен сегодня?",
]


def _generate_questions(vault: VaultManager, profile_exists: bool, n: int = 5) -> list[str]:
    questions: list[str] = []

    recent = vault.get_recent_notes(days=7)
    if recent:
        topics = extract_main_topics(recent[:10])
        if topics:
            questions.append(f"Какой прогресс по теме «{topics[0]}»?")

    daily_notes = vault.get_notes_in_folder(vault.config.folders.daily)
    if daily_notes:
        # Discover recurring keywords in recent journal entries
        recent_journals = sorted(
            daily_notes, key=lambda n: n.modified or datetime.min, reverse=True
        )[:5]
        recurring = extract_keywords(" ".join(n.content for n in recent_journals), top_n=3)
        if len(recurring) > 1:
            questions.append(f"Как обстоят дела с «{recurring[0]}» сегодня?")

    pool = [q for q in _BASE_QUESTIONS if q not in questions]
    random.shuffle(pool)
    while len(questions) < n and pool:
        questions.append(pool.pop())

    return questions[:n]


def _collect_answers(questions: list[str]) -> list[tuple[str, str]]:
    answers: list[tuple[str, str]] = []
    total = len(questions)
    for i, question in enumerate(questions, start=1):
        print(f"\nВопрос {i}/{total}: {question}")
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nЗапись прервана.")
            sys.exit(0)
        answers.append((question, answer))
    return answers


def _find_connections(answers: list[tuple[str, str]], vault: VaultManager) -> list[dict]:
    combined_text = " ".join(a for _, a in answers)
    keywords = set(extract_keywords(combined_text, top_n=10))

    daily_notes = vault.get_notes_in_folder(vault.config.folders.daily)
    today = datetime.today().date()
    connections = []

    for note in daily_notes:
        if note.modified and note.modified.date() == today:
            continue
        note_kws = set(extract_keywords(note.content, top_n=10))
        overlap = keywords & note_kws
        if len(overlap) < 2:
            continue
        days_ago = (today - note.modified.date()).days if note.modified else 0
        connections.append({
            "note": note,
            "days_ago": days_ago,
            "common_keywords": sorted(overlap)[:4],
            "excerpt": _relevant_excerpt(note.content, overlap),
        })

    # Sort by temporal proximity to round numbers (7, 30, 365)
    def proximity(c: dict) -> int:
        d = c["days_ago"]
        for anchor in (7, 30, 365):
            if abs(d - anchor) <= 5:
                return 0
        return d

    connections.sort(key=proximity)
    return connections[:3]


def _relevant_excerpt(content: str, keywords: set[str], length: int = 120) -> str:
    lower = content.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1:
            start = max(0, idx - 20)
            snippet = content[start: start + length].replace("\n", " ").strip()
            return f'"{snippet}..."'
    return f'"{content[:length].replace(chr(10), " ").strip()}..."'


def _generate_title(answers: list[tuple[str, str]]) -> str:
    combined = " ".join(a for _, a in answers)
    kws = extract_keywords(combined, top_n=3)
    if kws:
        title = " ".join(kw.capitalize() for kw in kws[:3])
        return title
    return "Дневниковая запись"


def _format_connections(connections: list[dict]) -> str:
    if not connections:
        return "_Связей с прошлыми записями не найдено._"
    lines = []
    for conn in connections:
        note = conn["note"]
        days = conn["days_ago"]
        date_str = note.modified.strftime("%d.%m.%Y") if note.modified else "?"
        excerpt = conn["excerpt"]
        kws_str = ", ".join(conn["common_keywords"])
        lines.append(f"**{days} дней назад ({date_str}): [[{note.path.stem}]]**")
        lines.append(f"{excerpt}")
        lines.append(f"_Общие темы: {kws_str}_\n")
    return "\n".join(lines)


def _create_daily_note(
    answers: list[tuple[str, str]],
    connections: list[dict],
    vault: VaultManager,
) -> Path:
    title = _generate_title(answers)
    date_str = datetime.today().strftime("%d-%m-%Y")
    filename = f"{date_str} - {title}.md"

    daily_dir = vault.root / vault.config.folders.daily
    daily_dir.mkdir(parents=True, exist_ok=True)
    filepath = daily_dir / filename

    qa_lines = "\n\n".join(
        f"**{q}**\n{a}" for q, a in answers
    )

    content = f"""\
---
created: {datetime.today().isoformat()}
tags:
  - личное/дневник
---

# {title}

{qa_lines}

## Связи с прошлым

{_format_connections(connections)}

---
#личное/дневник
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath


def run_daily_journal(
    config: Config,
    questions_count: int = 5,
    find_connections: bool = True,
    no_create: bool = False,
) -> None:
    try:
        vault = VaultManager(config)
    except VaultNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    today_str = datetime.today().strftime("%d.%m.%Y")
    print(f"\n📝 Дневниковая запись на {today_str}\n")
    print(_SEP)

    questions = _generate_questions(vault, profile_exists=False, n=questions_count)

    if no_create:
        print("Вопросы для сегодняшней записи:\n")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        return

    answers = _collect_answers(questions)

    connections = []
    if find_connections:
        print(f"\n{_SEP}\n🔗 Ищу связи с прошлыми записями...")
        connections = _find_connections(answers, vault)

    if connections:
        print(f"\n🔗 Нашёл связи с прошлыми записями:\n")
        for conn in connections:
            note = conn["note"]
            days = conn["days_ago"]
            date_str = note.modified.strftime("%d.%m.%Y") if note.modified else "?"
            print(f"📅 {days} дней назад ({date_str}):")
            print(f"   {conn['excerpt']}")
            print(f"   → Общие темы: {', '.join(conn['common_keywords'])}\n")
    else:
        print("\nСвязей с прошлыми записями не найдено.")

    print(_SEP)
    filepath = _create_daily_note(answers, connections, vault)
    print(f"\n✅ Создана заметка: {filepath.relative_to(vault.root)}")
