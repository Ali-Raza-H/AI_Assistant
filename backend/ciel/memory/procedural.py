from __future__ import annotations

import json
import time
import uuid
from typing import Any

from backend.ciel.memory.database.sqlite import MemoryDatabase


class ProceduralMemory:
    def __init__(self, database: MemoryDatabase):
        self.database = database

    def remember_procedure(
        self,
        name: str,
        description: str | None = None,
        trigger_conditions: dict[str, Any] | None = None,
        steps: list[dict[str, Any]] | None = None,
        related_entities: list[str] | None = None,
        confidence: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not name.strip():
            raise ValueError("Procedural memories require a name")
        now = time.time()
        procedure_id = uuid.uuid4().hex
        self.database.execute(
            """
            INSERT INTO procedures (
                id, name, description, trigger_conditions, steps,
                related_entities, confidence, created_at, updated_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                procedure_id,
                name,
                description,
                json.dumps(trigger_conditions or {}),
                json.dumps(steps or []),
                json.dumps(related_entities or []),
                confidence,
                now,
                now,
                json.dumps(metadata or {}),
            ),
        )
        return procedure_id

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2]
        rows = self.database.fetch_all(
            """
            SELECT * FROM procedures
            WHERE status = 'active'
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ?
            """,
            (max(limit * 4, limit),),
        )
        matches = []
        for row in rows:
            text = f"{row.get('name')} {row.get('description') or ''}".lower()
            if not terms or any(term in text for term in terms):
                matches.append(row)
        return matches[:limit]
