from __future__ import annotations

import math
import time


def memory_score(
    semantic_relevance: float,
    importance: float,
    recency_factor: float,
    reinforcement_factor: float,
) -> float:
    return (
        max(0.0, semantic_relevance)
        * min(1.0, max(0.0, importance))
        * min(1.0, max(0.0, recency_factor))
        * max(1.0, reinforcement_factor)
    )


def memory_recency_factor(
    timestamp: float | None,
    *,
    now: float | None = None,
    half_life_days: float = 90.0,
    floor: float = 0.2,
) -> float:
    if timestamp is None:
        return 1.0
    now = time.time() if now is None else now
    age_seconds = max(0.0, now - float(timestamp))
    half_life_seconds = max(1.0, half_life_days * 86400.0)
    decay = math.pow(0.5, age_seconds / half_life_seconds)
    return min(1.0, max(floor, decay))
