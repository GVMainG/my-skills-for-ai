from __future__ import annotations

import re
from collections import Counter
from math import log, sqrt


def tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer, lowercased."""
    return re.findall(r'[a-zа-яё0-9]+', text.lower())


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Jaccard similarity between two texts based on token sets."""
    set1 = set(tokenize(text1))
    set2 = set(tokenize(text2))
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def calculate_cosine_similarity(text1: str, text2: str) -> float:
    """Cosine similarity using raw term frequency vectors."""
    tf1 = Counter(tokenize(text1))
    tf2 = Counter(tokenize(text2))
    common = set(tf1) & set(tf2)
    dot = sum(tf1[t] * tf2[t] for t in common)
    norm1 = sqrt(sum(v * v for v in tf1.values()))
    norm2 = sqrt(sum(v * v for v in tf2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def compute_jaccard_matrix(feature_sets: list[set]) -> list[list[float]]:
    """Compute pairwise Jaccard distance matrix (1 - similarity) for clustering."""
    n = len(feature_sets)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            s1, s2 = feature_sets[i], feature_sets[j]
            union = len(s1 | s2)
            jaccard = len(s1 & s2) / union if union > 0 else 0.0
            dist = 1.0 - jaccard
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


def calculate_keyword_overlap(kw1: list[str], kw2: list[str]) -> float:
    """Fraction of kw2 keywords that appear in kw1 (recall-style overlap)."""
    if not kw2:
        return 0.0
    s1 = set(k.lower() for k in kw1)
    s2 = set(k.lower() for k in kw2)
    return len(s1 & s2) / len(s2)
