from __future__ import annotations


def memory_score(
    semantic_relevance: float,
    importance: float,
    recency_factor: float,
    reinforcement_factor: float,
) -> float:
    return semantic_relevance * importance * recency_factor * reinforcement_factor
