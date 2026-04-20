from __future__ import annotations

import re

# Simple lexicon-based sentiment (Russian + English)
_POSITIVE: set[str] = {
    "хорошо", "отлично", "прекрасно", "люблю", "нравится", "радость", "счастье",
    "успех", "достижение", "понял", "решил", "получилось", "кайф", "здорово",
    "интересно", "прогресс", "работает", "помогло", "excellent", "great", "love",
    "good", "happy", "success", "achievement", "progress", "works", "solved",
    "понимание", "ясность", "эффективно", "удобно", "доволен",
}

_NEGATIVE: set[str] = {
    "плохо", "ужасно", "ненавижу", "не нравится", "грусть", "разочарование",
    "проблема", "ошибка", "не работает", "сложно", "непонятно", "провал",
    "тревога", "стресс", "беспокойство", "неуверенность", "impostor",
    "bad", "terrible", "hate", "problem", "error", "difficult", "confused",
    "anxiety", "stress", "failure", "broken", "frustrated",
}

_INTENSIFIERS: set[str] = {"очень", "крайне", "совсем", "абсолютно", "very", "extremely", "totally"}


def analyze_sentiment(text: str) -> float:
    """Return sentiment score in [-1.0, +1.0].

    Simple lexicon-based approach: counts positive/negative word hits,
    applies 1.5× weight for intensifier-adjacent words.
    """
    tokens = re.findall(r'[a-zа-яё]+', text.lower())
    score = 0.0
    for i, token in enumerate(tokens):
        multiplier = 1.5 if (i > 0 and tokens[i - 1] in _INTENSIFIERS) else 1.0
        if token in _POSITIVE:
            score += multiplier
        elif token in _NEGATIVE:
            score -= multiplier

    # Normalise to [-1, 1]
    total = len(tokens)
    if total == 0:
        return 0.0
    return max(-1.0, min(1.0, score / (total * 0.1 + 1)))


def classify_sentiment(score: float) -> str:
    if score > 0.3:
        return "позитивный"
    if score < -0.3:
        return "негативный"
    return "нейтральный"
