from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from ..analyzers.keyword_extractor import extract_keywords, extract_tech_mentions
from ..analyzers.sentiment_analyzer import analyze_sentiment
from ..core.note import Note
from ..core.tags import TagsManager
from ..utils.similarity import calculate_keyword_overlap


@dataclass
class SkillEntry:
    technology: str
    mentions: int
    level: str  # beginner | familiar | intermediate | expert
    notes: list[str] = field(default_factory=list)
    quotes: list[str] = field(default_factory=list)


@dataclass
class CognitiveStyle:
    dominant: str
    distribution: dict[str, float] = field(default_factory=dict)


@dataclass
class PersonalityTraits:
    top_traits: list[str] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)


@dataclass
class Contradiction:
    statement1: str
    statement2: str
    topic: str
    note1_path: str
    note2_path: str
    time_gap_days: int


@dataclass
class PsychologicalPortrait:
    cognitive_style: CognitiveStyle
    personality_traits: PersonalityTraits
    values: list[str] = field(default_factory=list)
    behavioral_patterns: dict[str, str] = field(default_factory=dict)
    contradictions: list[Contradiction] = field(default_factory=list)


class SemanticAnalyzer:
    """Performs deep semantic analysis of vault notes."""

    def __init__(self, tags_manager: TagsManager) -> None:
        self.tags_manager = tags_manager

    # ------------------------------------------------------------------
    # Tag mapping
    # ------------------------------------------------------------------

    def map_keywords_to_tags(
        self, keywords: list[str], threshold: float = 0.3
    ) -> list[tuple[str, float]]:
        candidates = []
        for tag in self.tags_manager.all_tags:
            tag_keywords = self.tags_manager.get_keywords_for_tag(tag)
            if not tag_keywords:
                continue
            score = calculate_keyword_overlap(keywords, tag_keywords)
            if score > threshold:
                candidates.append((tag, score))
        return sorted(candidates, key=lambda x: x[1], reverse=True)[:5]

    # ------------------------------------------------------------------
    # Technical skills
    # ------------------------------------------------------------------

    def extract_technical_skills(self, notes: list[Note]) -> dict[str, SkillEntry]:
        skills: dict[str, SkillEntry] = {}
        for note in notes:
            techs = extract_tech_mentions(note.content)
            for tech in techs:
                key = tech.lower()
                if key not in skills:
                    skills[key] = SkillEntry(technology=tech, mentions=0, level="beginner")
                skills[key].mentions += 1
                skills[key].notes.append(note.filename)
                quote = self._extract_quote_with_tech(note.content, tech)
                if quote:
                    skills[key].quotes.append(f"{quote} ({note.modified.strftime('%d.%m.%Y') if note.modified else '?'})")

        for entry in skills.values():
            m = entry.mentions
            if m >= 10:
                entry.level = "expert"
            elif m >= 5:
                entry.level = "intermediate"
            elif m >= 2:
                entry.level = "familiar"
            else:
                entry.level = "beginner"

        return skills

    def _extract_quote_with_tech(self, content: str, tech: str) -> str | None:
        pattern = re.compile(re.escape(tech), re.IGNORECASE)
        for sentence in re.split(r'[.!?\n]', content):
            if pattern.search(sentence) and 20 < len(sentence.strip()) < 200:
                return sentence.strip()
        return None

    # ------------------------------------------------------------------
    # Psychological portrait
    # ------------------------------------------------------------------

    def build_psychological_portrait(self, notes: list[Note]) -> PsychologicalPortrait:
        cognitive = self._analyze_cognitive_style(notes)
        traits = self._extract_personality_traits(notes)
        values = self._extract_values(notes)
        patterns = self._find_behavioral_patterns(notes)
        contradictions = self._find_contradictions(notes)
        return PsychologicalPortrait(
            cognitive_style=cognitive,
            personality_traits=traits,
            values=values,
            behavioral_patterns=patterns,
            contradictions=contradictions,
        )

    def _analyze_cognitive_style(self, notes: list[Note]) -> CognitiveStyle:
        indicators = {
            "systematic": ["план", "структура", "алгоритм", "этап", "последовательно", "система"],
            "intuitive": ["чувствую", "кажется", "интуиция", "догадка", "ощущение"],
            "analytical": ["анализ", "разобрать", "компоненты", "детали", "разложить"],
            "holistic": ["общая картина", "в целом", "взаимосвязь", "контекст", "целостно"],
        }
        scores: dict[str, int] = {k: 0 for k in indicators}
        for note in notes:
            lower = note.content.lower()
            for style, kws in indicators.items():
                for kw in kws:
                    scores[style] += lower.count(kw)
        total = sum(scores.values()) or 1
        distribution = {k: round(v / total * 100, 1) for k, v in scores.items()}
        dominant = max(scores, key=scores.get)
        return CognitiveStyle(dominant=dominant, distribution=distribution)

    def _extract_personality_traits(self, notes: list[Note]) -> PersonalityTraits:
        patterns: dict[str, list[str]] = {
            "introversion": ["один", "тишина", "сосредоточиться", "уединение", "одиночество"],
            "extraversion": ["общение", "люди", "вместе", "компания", "команда"],
            "conscientiousness": ["организованно", "план", "дисциплина", "порядок", "структура"],
            "openness": ["новое", "идея", "творчество", "эксперимент", "инновация"],
            "neuroticism": ["тревога", "беспокойство", "стресс", "волнение", "переживание"],
        }
        scores: dict[str, int] = {k: 0 for k in patterns}
        for note in notes:
            lower = note.content.lower()
            for trait, kws in patterns.items():
                for kw in kws:
                    scores[trait] += lower.count(kw)
        top = [t for t, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]]
        return PersonalityTraits(top_traits=top, scores=scores)

    def _extract_values(self, notes: list[Note]) -> list[str]:
        value_patterns = {
            "профессиональный рост": ["экспертиза", "карьера", "рост", "обучение", "мастерство"],
            "автономность": ["self-hosted", "контроль", "независимость", "под капотом"],
            "системность": ["структура", "организация", "система", "порядок"],
            "творчество": ["творчество", "поэзия", "создание", "контент"],
            "долгосрочность": ["десятилетиями", "навсегда", "долгосрочно", "архив знаний"],
        }
        totals: dict[str, int] = {k: 0 for k in value_patterns}
        for note in notes:
            lower = note.content.lower()
            for val, kws in value_patterns.items():
                for kw in kws:
                    totals[val] += lower.count(kw)
        return [v for v, _ in sorted(totals.items(), key=lambda x: x[1], reverse=True) if totals[v] > 0]

    def _find_behavioral_patterns(self, notes: list[Note]) -> dict[str, str]:
        stress_indicators = ["тревожно", "структурир", "план", "стресс"]
        motivation_indicators = ["прогресс", "понял", "щёлкнуло", "работает", "решил"]
        patterns = {}
        stress_notes = [n for n in notes if any(w in n.content.lower() for w in stress_indicators)]
        if stress_notes:
            patterns["stress_response"] = "Систематизация и планирование как способ справиться"
        motivation_notes = [n for n in notes if any(w in n.content.lower() for w in motivation_indicators)]
        if motivation_notes:
            patterns["motivation"] = "Прогресс в понимании сложных тем и создание работающих систем"
        return patterns

    def _find_contradictions(self, notes: list[Note]) -> list[Contradiction]:
        """Detect contradictory sentiments about the same topic across notes."""
        contradictions = []
        statements: list[tuple[str, Note, float]] = []

        for note in notes:
            for sentence in re.split(r'[.!?\n]', note.content):
                s = sentence.strip()
                if len(s) < 20:
                    continue
                score = analyze_sentiment(s)
                if abs(score) > 0.4:
                    statements.append((s, note, score))

        # Compare pairs for same topic, opposite sentiment
        for i, (s1, n1, sc1) in enumerate(statements):
            for s2, n2, sc2 in statements[i + 1:]:
                if n1.path == n2.path:
                    continue
                if (sc1 > 0.4 and sc2 < -0.4) or (sc1 < -0.4 and sc2 > 0.4):
                    kw1 = set(extract_keywords(s1, 5))
                    kw2 = set(extract_keywords(s2, 5))
                    if len(kw1 & kw2) >= 2:
                        topic = ", ".join(sorted(kw1 & kw2)[:2])
                        gap = 0
                        if n1.modified and n2.modified:
                            gap = abs((n2.modified - n1.modified).days)
                        contradictions.append(Contradiction(
                            statement1=s1[:200],
                            statement2=s2[:200],
                            topic=topic,
                            note1_path=str(n1.path),
                            note2_path=str(n2.path),
                            time_gap_days=gap,
                        ))
                        if len(contradictions) >= 5:
                            return contradictions
        return contradictions
