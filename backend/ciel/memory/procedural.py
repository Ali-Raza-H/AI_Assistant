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
        name = name.strip()
        if not name:
            raise ValueError("Procedural memories require a name")
        if steps is not None and not isinstance(steps, list):
            raise ValueError("Procedure steps must be a list")
        confidence = min(1.0, max(0.0, float(confidence)))
        now = time.time()
        trigger_json = json.dumps(trigger_conditions or {})
        steps_json = json.dumps(steps or [])
        related_json = json.dumps(related_entities or [])
        metadata_json = json.dumps(metadata or {})

        existing = self.database.fetch_one(
            """
            SELECT id FROM procedures
            WHERE lower(name) = lower(?) AND status = 'active'
            """,
            (name,),
        )
        if existing:
            self.database.execute(
                """
                UPDATE procedures
                SET description = COALESCE(?, description),
                    trigger_conditions = CASE WHEN ? = '{}' THEN trigger_conditions ELSE ? END,
                    steps = CASE WHEN ? = '[]' THEN steps ELSE ? END,
                    related_entities = CASE WHEN ? = '[]' THEN related_entities ELSE ? END,
                    confidence = MAX(confidence, ?),
                    updated_at = ?,
                    metadata = CASE WHEN ? = '{}' THEN metadata ELSE ? END
                WHERE id = ?
                """,
                (
                    description,
                    trigger_json,
                    trigger_json,
                    steps_json,
                    steps_json,
                    related_json,
                    related_json,
                    confidence,
                    now,
                    metadata_json,
                    metadata_json,
                    existing["id"],
                ),
            )
            return existing["id"]

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
                trigger_json,
                steps_json,
                related_json,
                confidence,
                now,
                now,
                metadata_json,
            ),
        )
        return procedure_id

    def record_outcome(self, procedure_id: str, success: bool) -> None:
        row = self.database.fetch_one(
            "SELECT id, confidence FROM procedures WHERE id = ? AND status = 'active'",
            (procedure_id,),
        )
        if row is None:
            raise ValueError(f"Unknown active procedure: {procedure_id}")

        now = time.time()
        confidence = float(row.get("confidence") or 0.5)
        if success:
            confidence = min(1.0, confidence + 0.05)
            self.database.execute(
                """
                UPDATE procedures
                SET success_count = success_count + 1,
                    confidence = ?, last_used = ?, updated_at = ?
                WHERE id = ?
                """,
                (confidence, now, now, procedure_id),
            )
        else:
            confidence = max(0.0, confidence - 0.10)
            self.database.execute(
                """
                UPDATE procedures
                SET failure_count = failure_count + 1,
                    confidence = ?, last_used = ?, updated_at = ?
                WHERE id = ?
                """,
                (confidence, now, now, procedure_id),
            )

    def archive(self, procedure_id: str) -> None:
        self.database.execute(
            "UPDATE procedures SET status = 'archived', updated_at = ? WHERE id = ?",
            (time.time(), procedure_id),
        )

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        limit = max(1, int(limit))
        terms = [term for term in query.lower().split() if len(term) > 2]
        rows = self.database.fetch_all(
            """
            SELECT * FROM procedures
            WHERE status = 'active'
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ?
            """,
            (max(limit * 6, limit),),
        )
        matches = []
        for row in rows:
            trigger_text = json.dumps(row.get("trigger_conditions") or {})
            steps_text = json.dumps(row.get("steps") or [])
            text = (
                f"{row.get('name')} {row.get('description') or ''} "
                f"{trigger_text} {steps_text}"
            ).lower()
            lexical_score = sum(1 for term in terms if term in text)
            if lexical_score or not terms:
                row["_score"] = lexical_score + float(row.get("confidence") or 0)
                matches.append(row)
        matches.sort(key=lambda item: float(item.get("_score") or 0), reverse=True)
        return matches[:limit]
