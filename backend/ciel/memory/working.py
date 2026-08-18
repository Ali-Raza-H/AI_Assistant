from __future__ import annotations

from typing import Any


class WorkingMemory:
    def create(self, objective: str) -> dict[str, Any]:
        return {
            "objective": objective,
            "temporary_conclusions": [],
            "active_assumptions": [],
        }

    def reduce(self, memory: dict[str, Any], limit: int = 8) -> dict[str, Any]:
        reduced = dict(memory)
        for key, value in list(reduced.items()):
            if isinstance(value, list):
                reduced[key] = value[-limit:]
        return reduced

    def clear(self, memory: dict[str, Any]) -> None:
        memory.clear()
