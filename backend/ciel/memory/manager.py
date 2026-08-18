from __future__ import annotations

import json
import time
import uuid
from typing import Any

from backend.ciel.context.interaction import InteractionContext
from backend.ciel.memory.classifier import MemoryClassifier
from backend.ciel.memory.consolidation import MemoryConsolidation
from backend.ciel.memory.database.sqlite import MemoryDatabase
from backend.ciel.memory.entities import EntityMemory
from backend.ciel.memory.episodic import EpisodicMemory
from backend.ciel.memory.procedural import ProceduralMemory
from backend.ciel.memory.retrieval import MemoryRetrieval
from backend.ciel.memory.semantic import SemanticMemory
from backend.ciel.memory.vector.embeddings import HashEmbeddingProvider
from backend.ciel.memory.vector.store import SQLiteVectorStore
from backend.ciel.memory.working import WorkingMemory
from backend.ciel.runtime.logging import log


class MemoryManager:
    def __init__(self, database: MemoryDatabase | None = None):
        self.database = database or MemoryDatabase()
        self.working = WorkingMemory()
        self.embedding_provider = HashEmbeddingProvider()
        self.episodic_vectors = SQLiteVectorStore(
            self.database,
            self.embedding_provider,
            scope="episodic",
        )
        self.episodic = EpisodicMemory(self.database, self.episodic_vectors)
        self.semantic = SemanticMemory(self.database)
        self.entities = EntityMemory(self.database)
        self.procedural = ProceduralMemory(self.database)
        self.retrieval = MemoryRetrieval()
        self.classifier = MemoryClassifier()
        self.consolidation = MemoryConsolidation()

    def remember(self, data: dict[str, Any]) -> str | None:
        memory_type = data.get("type")
        if memory_type in {"episode", "episode_candidate"}:
            return self.episodic.remember_episode(
                summary=data.get("summary") or data.get("description") or "",
                session_id=data.get("session_id"),
                topics=data.get("topics"),
                related_project=data.get("related_project"),
                importance=float(data.get("importance", 0.5)),
                source_message_ids=data.get("source_message_ids"),
                metadata=data,
            )
        if memory_type in {"fact", "semantic_fact", "project_fact", "preference"}:
            return self.semantic.remember_fact(
                subject=str(data.get("subject") or ""),
                predicate=str(data.get("predicate") or ""),
                object_value=str(data.get("object") or data.get("object_value") or ""),
                confidence=float(data.get("confidence", 0.7)),
                source=data.get("source"),
                metadata=data,
            )
        if memory_type == "entity":
            return self.entities.remember_entity(
                entity_type=str(data.get("entity_type") or data.get("type_name") or "Unknown"),
                name=str(data.get("name") or ""),
                description=data.get("description"),
                metadata=data,
            )
        if memory_type == "relationship":
            return self.entities.remember_relationship(
                source_entity_id=str(data.get("source_entity_id") or ""),
                relation=str(data.get("relation") or data.get("predicate") or ""),
                target_entity_id=str(data.get("target_entity_id") or ""),
                confidence=float(data.get("confidence", 0.7)),
                source=data.get("source"),
                metadata=data,
            )
        if memory_type == "procedure":
            return self.procedural.remember_procedure(
                name=str(data.get("name") or ""),
                description=data.get("description"),
                trigger_conditions=data.get("trigger_conditions"),
                steps=data.get("steps"),
                related_entities=data.get("related_entities"),
                confidence=float(data.get("confidence", 0.5)),
                metadata=data,
            )
        return None

    def recall(
        self,
        query: str,
        scopes: list[str] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        scopes = scopes or ["episodic", "semantic", "entity", "procedural"]
        episodic = self.episodic.recall(query, limit) if "episodic" in scopes else []
        semantic = self.semantic.recall(query, limit) if "semantic" in scopes else []
        entities = (
            self.entities.recall(query, limit)
            if "entity" in scopes or "entities" in scopes
            else []
        )
        procedures = self.procedural.recall(query, limit) if "procedural" in scopes else []
        combined = self.retrieval.combine(episodic, semantic, entities, procedures)
        return self._deduplicate_memories(combined)[:limit]

    def retrieve_context(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        query = str(request.get("query") or "").strip()
        if not query:
            return []
        try:
            limit = max(1, min(50, int(request.get("limit", 8))))
        except (TypeError, ValueError):
            limit = 8
        memories = self.recall(query, request.get("scopes"), limit=limit)
        for memory in memories:
            if memory.get("scope") == "episodic" and isinstance(memory.get("id"), str):
                self.reinforce(memory["id"])
        return memories

    def consolidate(self) -> list[dict]:
        return self.consolidation.consolidate()

    def reinforce(self, memory_id: str) -> None:
        self.episodic.reinforce(memory_id)

    def forget(self, memory_id: str | None = None) -> None:
        if memory_id:
            self.database.execute(
                "UPDATE episodic_memories SET status = 'archived' WHERE id = ?",
                (memory_id,),
            )

    def resolve_conflicts(self) -> list[dict]:
        return []

    def recent_conversation(
        self,
        limit: int = 12,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        limit = max(1, int(limit))
        if session_id:
            rows = self.database.fetch_all(
                """
                SELECT role, content, created_at, interaction_id
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (session_id, limit),
            )
        else:
            rows = self.database.fetch_all(
                """
                SELECT role, content, created_at, interaction_id
                FROM messages
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
        return list(reversed(rows))

    def load_chat_history(self, limit: int | None = None) -> list[dict[str, str]]:
        if limit is None:
            rows = self.database.fetch_all(
                """
                SELECT user_message, assistant_response, completed_at
                FROM interactions
                WHERE assistant_response IS NOT NULL
                ORDER BY completed_at ASC
                """
            )
        else:
            rows = self.database.fetch_all(
                """
                SELECT user_message, assistant_response, completed_at
                FROM (
                    SELECT user_message, assistant_response, completed_at
                    FROM interactions
                    WHERE assistant_response IS NOT NULL
                    ORDER BY completed_at DESC
                    LIMIT ?
                )
                ORDER BY completed_at ASC
                """,
                (max(1, int(limit)),),
            )
        return [
            {
                "userMessage": row["user_message"],
                "assistantResponse": row["assistant_response"],
            }
            for row in rows
        ]

    def save_chat_exchange(
        self,
        user_message: str,
        assistant_response: str,
        session_id: str = "default",
        interaction_id: str | None = None,
    ) -> str:
        now = time.time()
        interaction_id = interaction_id or uuid.uuid4().hex
        self.database.ensure_session(session_id)
        self.database.execute(
            """
            INSERT INTO interactions (
                id, session_id, user_message, assistant_response,
                status, started_at, completed_at, metadata
            )
            VALUES (?, ?, ?, ?, 'complete', ?, ?, '{}')
            ON CONFLICT(id) DO UPDATE SET
                assistant_response = excluded.assistant_response,
                status = excluded.status,
                completed_at = excluded.completed_at
            """,
            (interaction_id, session_id, user_message, assistant_response, now, now),
        )
        self._save_message(interaction_id, session_id, "user", user_message, now)
        self._save_message(
            interaction_id,
            session_id,
            "assistant",
            assistant_response,
            now + 0.001,
        )
        return interaction_id

    def persist_interaction(self, context: InteractionContext) -> None:
        self.database.ensure_session(context.session_id)
        metadata = context.to_record()
        assistant_response = context.final_response or ""
        self.database.execute(
            """
            INSERT INTO interactions (
                id, session_id, user_message, assistant_response,
                status, started_at, completed_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                assistant_response = excluded.assistant_response,
                status = excluded.status,
                completed_at = excluded.completed_at,
                metadata = excluded.metadata
            """,
            (
                context.interaction_id,
                context.session_id,
                context.user_message,
                assistant_response,
                context.status,
                context.started_at,
                context.completed_at or time.time(),
                json.dumps(metadata),
            ),
        )
        self._save_message(
            context.interaction_id,
            context.session_id,
            "user",
            context.user_message,
            context.started_at,
        )
        if context.final_response:
            self._save_message(
                context.interaction_id,
                context.session_id,
                "assistant",
                context.final_response,
                context.completed_at or time.time(),
            )

    def evaluate_interaction(self, context: InteractionContext) -> list[str]:
        committed = []
        for candidate in self.classifier.classify(context):
            try:
                memory_id = self.remember(
                    {
                        **candidate,
                        "session_id": context.session_id,
                        "source_interaction_id": context.interaction_id,
                    }
                )
            except (TypeError, ValueError) as error:
                log("warning", f"memory manager skipped invalid memory candidate: {error}")
                continue
            if memory_id:
                committed.append(memory_id)
        return committed

    def _deduplicate_memories(
        self,
        memories: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        deduplicated = []
        seen = set()
        for memory in memories:
            memory_id = memory.get("id")
            key = (memory.get("scope"), memory_id)
            if memory_id is None:
                key = (
                    memory.get("scope"),
                    memory.get("summary") or memory.get("subject") or str(memory),
                )
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(memory)
        return deduplicated

    def _save_message(
        self,
        interaction_id: str,
        session_id: str,
        role: str,
        content: str,
        created_at: float,
    ) -> None:
        message_id = f"{interaction_id}:{role}"
        self.database.execute(
            """
            INSERT INTO messages (id, interaction_id, session_id, role, content, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, '{}')
            ON CONFLICT(id) DO UPDATE SET content = excluded.content
            """,
            (message_id, interaction_id, session_id, role, content, created_at),
        )
