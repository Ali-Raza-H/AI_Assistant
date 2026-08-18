from __future__ import annotations

import json
import time
import uuid
from typing import Any

from backend.ciel.memory.database.sqlite import MemoryDatabase


class EntityMemory:
    def __init__(self, database: MemoryDatabase):
        self.database = database

    def remember_entity(
        self,
        entity_type: str,
        name: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not entity_type.strip() or not name.strip():
            raise ValueError("Entities require type and name")
        now = time.time()
        existing = self.database.fetch_one(
            "SELECT id FROM entities WHERE type = ? AND name = ?",
            (entity_type, name),
        )
        if existing:
            self.database.execute(
                """
                UPDATE entities
                SET description = COALESCE(?, description), updated_at = ?
                WHERE id = ?
                """,
                (description, now, existing["id"]),
            )
            return existing["id"]

        entity_id = uuid.uuid4().hex
        self.database.execute(
            """
            INSERT INTO entities (id, type, name, description, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (entity_id, entity_type, name, description, now, now, json.dumps(metadata or {})),
        )
        return entity_id

    def remember_relationship(
        self,
        source_entity_id: str,
        relation: str,
        target_entity_id: str,
        confidence: float = 0.7,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not source_entity_id.strip() or not relation.strip() or not target_entity_id.strip():
            raise ValueError("Relationships require source, relation, and target")
        now = time.time()
        relationship_id = uuid.uuid4().hex
        self.database.execute(
            """
            INSERT INTO relationships (
                id, source_entity_id, relation, target_entity_id, confidence,
                source, created_at, valid_from, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                relationship_id,
                source_entity_id,
                relation,
                target_entity_id,
                confidence,
                source,
                now,
                now,
                json.dumps(metadata or {}),
            ),
        )
        return relationship_id

    def recall(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2]
        rows = self.database.fetch_all(
            "SELECT * FROM entities ORDER BY updated_at DESC LIMIT ?",
            (max(limit * 4, limit),),
        )
        matches = []
        for row in rows:
            text = f"{row.get('type')} {row.get('name')} {row.get('description') or ''}".lower()
            if not terms or any(term in text for term in terms):
                matches.append(row)
        return matches[:limit]
