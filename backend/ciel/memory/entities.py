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
        entity_type = entity_type.strip()
        name = name.strip()
        if not entity_type or not name:
            raise ValueError("Entities require type and name")
        now = time.time()
        existing = self.database.fetch_one(
            "SELECT id FROM entities WHERE lower(type) = lower(?) AND lower(name) = lower(?)",
            (entity_type, name),
        )
        if existing:
            self.database.execute(
                """
                UPDATE entities
                SET description = COALESCE(?, description),
                    updated_at = ?,
                    metadata = CASE WHEN ? = '{}' THEN metadata ELSE ? END
                WHERE id = ?
                """,
                (
                    description,
                    now,
                    json.dumps(metadata or {}),
                    json.dumps(metadata or {}),
                    existing["id"],
                ),
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
        source_entity_id = source_entity_id.strip()
        relation = relation.strip()
        target_entity_id = target_entity_id.strip()
        if not source_entity_id or not relation or not target_entity_id:
            raise ValueError("Relationships require source, relation, and target")

        for entity_id in (source_entity_id, target_entity_id):
            if self.database.fetch_one("SELECT id FROM entities WHERE id = ?", (entity_id,)) is None:
                raise ValueError(f"Relationship references unknown entity: {entity_id}")

        confidence = min(1.0, max(0.0, float(confidence)))
        now = time.time()
        existing = self.database.fetch_one(
            """
            SELECT id FROM relationships
            WHERE source_entity_id = ? AND relation = ? AND target_entity_id = ?
              AND status = 'active' AND valid_until IS NULL
            """,
            (source_entity_id, relation, target_entity_id),
        )
        if existing:
            self.database.execute(
                """
                UPDATE relationships
                SET confidence = MAX(confidence, ?),
                    source = COALESCE(?, source),
                    metadata = CASE WHEN ? = '{}' THEN metadata ELSE ? END
                WHERE id = ?
                """,
                (
                    confidence,
                    source,
                    json.dumps(metadata or {}),
                    json.dumps(metadata or {}),
                    existing["id"],
                ),
            )
            return existing["id"]

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
        scan_limit = max(limit * 4, limit)
        entity_rows = self.database.fetch_all(
            "SELECT * FROM entities ORDER BY updated_at DESC LIMIT ?",
            (scan_limit,),
        )
        relationship_rows = self.database.fetch_all(
            """
            SELECT
                r.*,
                s.name AS source_name,
                s.type AS source_type,
                t.name AS target_name,
                t.type AS target_type
            FROM relationships r
            JOIN entities s ON s.id = r.source_entity_id
            JOIN entities t ON t.id = r.target_entity_id
            WHERE r.status = 'active'
            ORDER BY r.created_at DESC
            LIMIT ?
            """,
            (scan_limit,),
        )

        matches = []
        for row in entity_rows:
            text = f"{row.get('type')} {row.get('name')} {row.get('description') or ''}".lower()
            score = sum(1 for term in terms if term in text)
            if score or not terms:
                matches.append({"kind": "entity", "_score": score + 0.25, **row})

        for row in relationship_rows:
            text = (
                f"{row.get('source_type')} {row.get('source_name')} "
                f"{row.get('relation')} {row.get('target_type')} {row.get('target_name')}"
            ).lower()
            score = sum(1 for term in terms if term in text)
            if score or not terms:
                matches.append(
                    {
                        "kind": "relationship",
                        "_score": score + float(row.get("confidence") or 0),
                        **row,
                    }
                )

        matches.sort(key=lambda item: float(item.get("_score") or 0), reverse=True)
        return matches[:limit]
