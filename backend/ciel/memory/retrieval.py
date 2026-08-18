from __future__ import annotations

from typing import Any


class MemoryRetrieval:
    def combine(
        self,
        episodic: list[dict[str, Any]],
        semantic: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        procedures: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        context = []
        context.extend({"scope": "episodic", **item} for item in episodic)
        context.extend({"scope": "semantic", **item} for item in semantic)
        context.extend({"scope": "entity", **item} for item in entities)
        context.extend({"scope": "procedural", **item} for item in procedures)
        return context
