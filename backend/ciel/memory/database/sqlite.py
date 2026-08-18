from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from backend.ciel.runtime.settings import MEMORY_DB_PATH


class MemoryDatabase:
    def __init__(self, path: Path | None = None):
        self.path = path or MEMORY_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection: sqlite3.Connection | None = sqlite3.connect(
            self.path,
            check_same_thread=False,
            timeout=10,
        )
        self._connection.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        with self._lock:
            connection = self._require_connection()
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                PRAGMA foreign_keys = ON;
                PRAGMA busy_timeout = 10000;

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    summary TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    assistant_response TEXT,
                    status TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    interaction_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(interaction_id) REFERENCES interactions(id),
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS episodic_memories (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp REAL NOT NULL,
                    summary TEXT NOT NULL,
                    topics TEXT NOT NULL DEFAULT '[]',
                    related_project TEXT,
                    importance REAL NOT NULL DEFAULT 0.5,
                    source_message_ids TEXT NOT NULL DEFAULT '[]',
                    access_count INTEGER NOT NULL DEFAULT 0,
                    last_accessed REAL,
                    memory_strength REAL NOT NULL DEFAULT 0.5,
                    status TEXT NOT NULL DEFAULT 'active',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS memory_vectors (
                    memory_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS semantic_facts (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    source TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    valid_from REAL,
                    valid_until REAL,
                    status TEXT NOT NULL DEFAULT 'active',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_entity_id TEXT NOT NULL,
                    relation TEXT NOT NULL,
                    target_entity_id TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    source TEXT,
                    created_at REAL NOT NULL,
                    valid_from REAL,
                    valid_until REAL,
                    status TEXT NOT NULL DEFAULT 'active',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(source_entity_id) REFERENCES entities(id),
                    FOREIGN KEY(target_entity_id) REFERENCES entities(id)
                );

                CREATE TABLE IF NOT EXISTS procedures (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    trigger_conditions TEXT NOT NULL DEFAULT '{}',
                    steps TEXT NOT NULL DEFAULT '[]',
                    related_entities TEXT NOT NULL DEFAULT '[]',
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    confidence REAL NOT NULL DEFAULT 0.5,
                    last_used REAL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_created
                    ON messages(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_interactions_session_completed
                    ON interactions(session_id, completed_at);
                CREATE INDEX IF NOT EXISTS idx_episodes_status_time
                    ON episodic_memories(status, timestamp);
                CREATE INDEX IF NOT EXISTS idx_semantic_active_lookup
                    ON semantic_facts(subject, predicate, status, valid_until);
                CREATE INDEX IF NOT EXISTS idx_relationship_source
                    ON relationships(source_entity_id, relation, status);
                CREATE INDEX IF NOT EXISTS idx_relationship_target
                    ON relationships(target_entity_id, relation, status);
                """
            )
            connection.commit()

    def execute(self, query: str, parameters: tuple[Any, ...] = ()) -> None:
        with self._lock:
            connection = self._require_connection()
            connection.execute(query, parameters)
            connection.commit()

    def fetch_all(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._require_connection().execute(query, parameters).fetchall()
        return [self._decode_row(row) for row in rows]

    def fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...] = (),
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(query, parameters)
        return rows[0] if rows else None

    def ensure_session(self, session_id: str, title: str | None = None) -> None:
        now = time.time()
        self.execute(
            """
            INSERT INTO sessions (id, title, summary, created_at, updated_at)
            VALUES (?, ?, NULL, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                updated_at = excluded.updated_at,
                title = COALESCE(excluded.title, sessions.title)
            """,
            (session_id, title, now, now),
        )

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def _require_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise RuntimeError("Memory database connection is closed")
        return self._connection

    def _decode_row(self, row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for key in (
            "metadata",
            "topics",
            "source_message_ids",
            "trigger_conditions",
            "steps",
            "related_entities",
            "embedding",
        ):
            if key in result and isinstance(result[key], str):
                try:
                    result[key] = json.loads(result[key])
                except json.JSONDecodeError:
                    pass
        return result

    def __enter__(self) -> "MemoryDatabase":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
