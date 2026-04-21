from __future__ import annotations

import re
from collections import Counter
from math import log

# Russian and English stopwords (compact set)
_STOPWORDS: set[str] = {
    # Russian
    "и", "в", "не", "на", "что", "с", "по", "это", "как", "к", "из",
    "а", "о", "но", "то", "все", "от", "так", "же", "за", "при", "если",
    "было", "есть", "быть", "для", "или", "уже", "мне", "его", "ее", "их",
    "нет", "он", "она", "они", "мы", "вы", "я", "тот", "при", "со", "де",
    "этот", "которые", "который", "также", "когда", "чтобы", "только", "еще",
    "где", "да", "нас", "вас", "им", "до", "об", "во", "ни", "бы", "ну",
    # English
    "the", "a", "an", "is", "in", "it", "of", "and", "to", "that",
    "this", "for", "with", "are", "was", "be", "have", "at", "not",
    "but", "or", "by", "from", "on", "as", "we", "you", "i", "he",
    "she", "they", "do", "can", "will", "more", "has", "if", "what",
    "so", "which", "its", "then", "into", "than", "when", "their",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r'[a-zа-яё][a-zа-яё0-9+#.\-]*', text.lower())


def _filter(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """Extract top-N keywords by term frequency (no corpus IDF available)."""
    tokens = _filter(_tokenize(text))
    if not tokens:
        return []
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def extract_keywords_with_scores(text: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Return (keyword, normalized_tf) pairs."""
    tokens = _filter(_tokenize(text))
    if not tokens:
        return []
    counts = Counter(tokens)
    total = sum(counts.values())
    return [(w, c / total) for w, c in counts.most_common(top_n)]


def extract_tech_mentions(text: str) -> list[str]:
    """Extract technology/tool names from text using a curated regex list."""
    patterns = [
        r'\bC#\b', r'\.NET\b', r'\bASP\.NET\b', r'\bEF\s*Core\b',
        r'\bLinq\b', r'\bLINQ\b', r'\basync/await\b', r'\bTask\.Run\b',
        r'\bCancellationToken\b', r'\bConfigureAwait\b',
        r'\bDocker\b', r'\bdocker-compose\b', r'\bKubernetes\b', r'\bk8s\b',
        r'\bLinux\b', r'\bUbuntu\b', r'\bnginx\b', r'\bFRP\b',
        r'\bPython\b', r'\bJavaScript\b', r'\bTypeScript\b', r'\bRust\b',
        r'\bn8n\b', r'\bObsidian\b', r'\bClaude\b', r'\bGPT\b',
        r'\bSQL\b', r'\bPostgreSQL\b', r'\bRedis\b', r'\bMongoDB\b',
        r'\bgRPC\b', r'\bREST\b', r'\bgit\b', r'\bCI/CD\b',
        r'\bSOLID\b', r'\bDDD\b', r'\bMVC\b', r'\bClean\s*Architecture\b',
    ]
    found = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            found.add(m.group(0).strip())
    return sorted(found)


def extract_main_topics(notes: list) -> list[str]:
    """Extract dominant topics from a list of Note objects."""
    combined = " ".join(n.content for n in notes)
    return extract_keywords(combined, top_n=5)
