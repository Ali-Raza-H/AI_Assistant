import tempfile
import unittest
from pathlib import Path

from backend.ciel.context.interaction import InteractionContext
from backend.ciel.memory.database.sqlite import MemoryDatabase
from backend.ciel.memory.manager import MemoryManager


class MemoryManagerTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = MemoryDatabase(Path(self.tempdir.name) / "memory.db")
        self.manager = MemoryManager(self.database)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_episodic_memory_uses_vector_index_for_recall(self):
        memory_id = self.manager.remember(
            {
                "type": "episode",
                "summary": "The router model changed because structured JSON was more reliable.",
                "topics": ["router", "model"],
                "importance": 0.8,
            }
        )

        recalled = self.manager.retrieve_context(
            {"query": "Why did the routing model change?", "scopes": ["episodic"]}
        )
        vector_row = self.database.fetch_one(
            "SELECT memory_id, scope, embedding FROM memory_vectors WHERE memory_id = ?",
            (memory_id,),
        )

        self.assertTrue(any(memory["id"] == memory_id for memory in recalled))
        self.assertEqual(vector_row["scope"], "episodic")
        self.assertIsInstance(vector_row["embedding"], list)
        refreshed = self.database.fetch_one(
            "SELECT access_count FROM episodic_memories WHERE id = ?",
            (memory_id,),
        )
        self.assertEqual(refreshed["access_count"], 1)

    def test_trivial_completed_interaction_is_not_durable_memory(self):
        context = InteractionContext.create("hi", "interaction-1")
        context.finish("complete", "Hello.")

        committed = self.manager.evaluate_interaction(context)

        self.assertEqual(committed, [])
        rows = self.database.fetch_all("SELECT * FROM episodic_memories")
        self.assertEqual(rows, [])

    def test_semantic_fact_change_preserves_historical_fact(self):
        first_id = self.manager.remember(
            {
                "type": "semantic_fact",
                "subject": "CIEL Router",
                "predicate": "uses_model",
                "object": "Model A",
                "confidence": 0.7,
            }
        )
        second_id = self.manager.remember(
            {
                "type": "semantic_fact",
                "subject": "CIEL Router",
                "predicate": "uses_model",
                "object": "Model B",
                "confidence": 0.8,
            }
        )

        historical = self.database.fetch_one(
            "SELECT status, valid_until FROM semantic_facts WHERE id = ?",
            (first_id,),
        )
        active = self.database.fetch_one(
            "SELECT status, valid_until FROM semantic_facts WHERE id = ?",
            (second_id,),
        )

        self.assertEqual(historical["status"], "historical")
        self.assertIsNotNone(historical["valid_until"])
        self.assertEqual(active["status"], "active")
        self.assertIsNone(active["valid_until"])


if __name__ == "__main__":
    unittest.main()
