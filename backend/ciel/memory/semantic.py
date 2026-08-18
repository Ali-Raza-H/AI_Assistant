from __future__ import annotations

import json
import time
import uuid
from typing import Any

from backend.ciel.memory.database.sqlite import MemoryDatabase


TEMPORAL_QUERY_MARKERS = {
    "before",
    "previous",
    "previously",
    "former",
    "formerly",
    "old",
    "past",
    "history",
    "historical",
    "used",
}


class SemanticMemory:
    def __init__(self, database: MemoryDatabase):
        self.database = database

    def remember_fact(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        confidence: float = 0.7,
        source: str | None = None,
        valid_from: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        subject = subject.strip()
        predicate = predicate.strip()
        object_value = object_value.strip()
        if not subject or not predicate or not object_value:
            raise ValueError("Semantic facts require subject, predicate, and object")
        confidence = min(1.0, max(0.0, float(confidence)))
        now = time.time()
        metadata_json = json.dumps(metadata or {})

        duplicate = self.database.fetch_one(
            """
            SELECT id, confidence FROM semantic_facts
            WHERE lower(subject) = lower(?) AND lower(predicate) = lower(?)
              AND lower(object) = lower(?)
              AND status = 'active' AND valid_until IS NULL
            """,
            (subject, predicate, object_value),
        )
        if duplicate:
            self.database.execute(
                """
                UPDATE semantic_facts
                SET confidence = MAX(confidence, ?),
                    source = COALESCE(?, source),
                    updated_at = ?,
                    metadata = CASE WHEN ? = '{}' THEN metadata ELSE ? END
                WHERE id = ?
                """,
                (
                    confidence,
                    source,
                    now,
                    metadata_json,
                    metadata_json,
                    duplicate["id"],
                ),
            )
            return duplicate["id"]

        existing = self.database.fetch_all(
            """
            SELECT id FROM semantic_facts
            WHERE lower(subject) = lower(?) AND lower(predicate) = lower(?)
              AND status = 'active' AND valid_until IS NULL
              AND lower(object) != lower(?)
            """,
            (subject, predicate, object_value),
        )
        for fact in existing:
            self.database.execute(
                """
                UPDATE semantic_facts
                SET valid_until = ?, status = 'historical', updated_at = ?
                WHERE id = ?
                """,
                (valid_from or now, now, fact["id"]),
            )

        fact_id = uuid.uuid4().hex
        self.database.execute(
            """
            INSERT INTO semantic_facts (
                id, subject, predicate, object, confidence, source,
                created_at, updated_at, valid_from, valid_until, status, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', ?)
            """,
            (
                fact_id,
                subject,
                predicate,
                object_value,
                confidence,
                source,
                now,
                now,
                valid_from or now,
                metadata_json,
            ),
        )
        return fact_id

    def recall(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2]
        include_historical = bool(TEMPORAL_QUERY_MARKERS.intersection(terms))
        if include_historical:
            rows = self.database.fetch_all(
                """
                SELECT * FROM semantic_facts
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (max(limit * 6, limit),),
            )
        else:
            rows = self.database.fetch_all(
                """
                SELECT * FROM semantic_facts
                WHERE status = 'active'
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (max(limit * 4, limit),),
            )

        scored = []
        for row in rows:
            text = f"{row.get('subject')} {row.get('predicate')} {row.get('object')}".lower()
            lexical_score = sum(1 for term in terms if term in text)
            if lexical_score or not terms:
                active_bonus = 0.25 if row.get("status") == "active" and not include_historical else 0.0
                row["_score"] = lexical_score + float(row.get("confidence") or 0) + active_bonus
                scored.append(row)
        scored.sort(key=lambda item: item["_score"], reverse=True)
        return scored[:limit]
