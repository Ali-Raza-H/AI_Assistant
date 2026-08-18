from __future__ import annotations

import json
import time
import uuid
from typing import Any

from backend.ciel.memory.database.sqlite import MemoryDatabase
from backend.ciel.memory.scoring import memory_score
from backend.ciel.memory.vector.store import VectorStore


class EpisodicMemory:
    def __init__(self, database: MemoryDatabase, vector_store: VectorStore | None = None):
        self.database = database
        self.vector_store = vector_store

    def remember_episode(
        self,
        summary: str,
        session_id: str | None = None,
        topics: list[str] | None = None,
        related_project: str | None = None,
        importance: float = 0.5,
        source_message_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if not summary.strip():
            raise ValueError("Episodic memories require a summary")
        memory_id = uuid.uuid4().hex
        self.database.execute(
            """
            INSERT INTO episodic_memories (
                id, session_id, timestamp, summary, topics, related_project,
                importance, source_message_ids, memory_strength, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                session_id,
                time.time(),
                summary,
                json.dumps(topics or []),
                related_project,
                importance,
                json.dumps(source_message_ids or []),
                importance,
                json.dumps(metadata or {}),
            ),
        )
        if self.vector_store is not None and summary.strip():
            index_text = " ".join(
                part
                for part in (
                    summary,
                    " ".join(topics or []),
                    related_project or "",
                )
                if part
            )
            self.vector_store.upsert(memory_id, index_text)
        return memory_id

    def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = [term for term in query.lower().split() if len(term) > 2]
        rows = self.database.fetch_all(
            """
            SELECT * FROM episodic_memories
            WHERE status = 'active'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (max(limit * 4, limit),),
        )
        scored_by_id = {}
        for row in rows:
            text = " ".join(
                [
                    str(row.get("summary") or ""),
                    " ".join(row.get("topics") or []),
                    str(row.get("related_project") or ""),
                ]
            ).lower()
            lexical_score = sum(1 for term in terms if term in text)
            if lexical_score or not terms:
                row["_score"] = memory_score(
                    semantic_relevance=max(lexical_score, 1),
                    importance=float(row.get("importance") or 0.5),
                    recency_factor=1.0,
                    reinforcement_factor=1.0 + float(row.get("memory_strength") or 0.5),
                )
                scored_by_id[row["id"]] = row

        if self.vector_store is not None and query.strip():
            for hit in self.vector_store.search(query, limit=max(limit * 4, limit)):
                memory_id = hit.get("memory_id")
                if not isinstance(memory_id, str):
                    continue
                row = scored_by_id.get(memory_id) or self.database.fetch_one(
                    "SELECT * FROM episodic_memories WHERE id = ? AND status = 'active'",
                    (memory_id,),
                )
                if row is None:
                    continue
                vector_score = float(hit.get("_vector_score") or 0)
                row["_vector_score"] = vector_score
                row["_score"] = max(
                    float(row.get("_score") or 0),
                    memory_score(
                        semantic_relevance=max(vector_score, 0.01),
                        importance=float(row.get("importance") or 0.5),
                        recency_factor=1.0,
                        reinforcement_factor=1.0 + float(row.get("memory_strength") or 0.5),
                    ),
                )
                scored_by_id[memory_id] = row

        scored = list(scored_by_id.values())
        scored.sort(key=lambda item: item["_score"], reverse=True)
        return scored[:limit]

    def reinforce(self, memory_id: str) -> None:
        self.database.execute(
            """
            UPDATE episodic_memories
            SET access_count = access_count + 1,
                last_accessed = ?,
                memory_strength = MIN(memory_strength + 0.05, 1.0)
            WHERE id = ?
            """,
            (time.time(), memory_id),
        )
