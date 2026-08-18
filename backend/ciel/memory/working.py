from __future__ import annotations

from typing import Any


class WorkingMemory:
    def create(self, objective: str) -> dict[str, Any]:
        return {
            "objective": objective,
            "actions": [],
            "observations": [],
            "temporary_conclusions": [],
        }

    def reduce(self, memory: dict[str, Any], limit: int = 8) -> dict[str, Any]:
        reduced = dict(memory)
        for key in ("actions", "observations", "temporary_conclusions"):
            if isinstance(reduced.get(key), list):
                reduced[key] = reduced[key][-limit:]
        return reduced

    def clear(self, memory: dict[str, Any]) -> None:
        memory.clear()
