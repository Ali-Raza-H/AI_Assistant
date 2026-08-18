from __future__ import annotations

import json
import math
import time
from typing import Any

from backend.ciel.memory.database.sqlite import MemoryDatabase
from backend.ciel.memory.vector.embeddings import EmbeddingProvider, HashEmbeddingProvider


class VectorStore:
    def upsert(self, memory_id: str, text: str) -> None:
        raise NotImplementedError("Vector storage is a stage-2 extension point")

    def search(self, query: str, limit: int = 5) -> list[dict]:
        raise NotImplementedError("Vector retrieval is a stage-2 extension point")


class SQLiteVectorStore(VectorStore):
    def __init__(
        self,
        database: MemoryDatabase,
        embedding_provider: EmbeddingProvider | None = None,
        scope: str = "episodic",
    ):
        self.database = database
        self.embedding_provider = embedding_provider or HashEmbeddingProvider()
        self.scope = scope

    def upsert(self, memory_id: str, text: str) -> None:
        embedding = self.embedding_provider.embed(text)
        self.database.execute(
            """
            INSERT INTO memory_vectors (memory_id, scope, text, embedding, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(memory_id) DO UPDATE SET
                scope = excluded.scope,
                text = excluded.text,
                embedding = excluded.embedding,
                updated_at = excluded.updated_at
            """,
            (memory_id, self.scope, text, json.dumps(embedding), time.time()),
        )

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_embedding = self.embedding_provider.embed(query)
        if not any(query_embedding):
            return []

        rows = self.database.fetch_all(
            """
            SELECT memory_id, scope, text, embedding
            FROM memory_vectors
            WHERE scope = ?
            """,
            (self.scope,),
        )
        scored = []
        for row in rows:
            embedding = row.get("embedding")
            if not isinstance(embedding, list):
                continue
            score = self._cosine(query_embedding, embedding)
            if score > 0:
                scored.append({**row, "_vector_score": score})

        scored.sort(key=lambda item: item["_vector_score"], reverse=True)
        return scored[:limit]

    def _cosine(self, left: list[float], right: list[float]) -> float:
        size = min(len(left), len(right))
        if size == 0:
            return 0.0
        dot = sum(left[index] * right[index] for index in range(size))
        left_magnitude = math.sqrt(sum(value * value for value in left[:size]))
        right_magnitude = math.sqrt(sum(value * value for value in right[:size]))
        if left_magnitude == 0 or right_magnitude == 0:
            return 0.0
        return dot / (left_magnitude * right_magnitude)
