import unittest
from unittest.mock import Mock, patch

from backend.ciel.brain.schemas import (
    ACTION_REQUIRED,
    COMPLETE,
    FAILED,
    NEED_MEMORY,
    NEED_USER,
    BrainDecision,
)
from backend.ciel.context.interaction import InteractionContext
from backend.ciel.observations.normalizer import ObservationNormalizer


class InteractionContextTests(unittest.TestCase):
    def test_retrieved_memories_are_deduplicated_by_scope_and_id(self):
        context = InteractionContext.create("hello", "interaction-1", "session-1")
        context.add_retrieved_memories(
            [
                {"scope": "episodic", "id": "m1", "summary": "one"},
                {"scope": "episodic", "id": "m1", "summary": "duplicate"},
                {"scope": "semantic", "id": "m1", "summary": "different scope"},
            ]
        )
        self.assertEqual(len(context.retrieved_memories), 2)

    def test_actions_and_observations_are_not_duplicated_in_working_memory(self):
        context = InteractionContext.create("hello", "interaction-1", "session-1")
        context.add_action({"intent": "inspect"})
        context.add_observation({"summary": "done"})
        self.assertNotIn("actions", context.working_memory)
        self.assertNotIn("observations", context.working_memory)


class ObservationNormalizerTests(unittest.TestCase):
    def test_empty_route_is_not_success(self):
        normalizer = ObservationNormalizer()
        observation = normalizer.normalize(
            {"intent": "inspect_file"},
            {"flags": {"isLooping": False, "doRemember": False}, "tools": []},
            {"flags": {"isLooping": False, "doRemember": False}, "tools": [], "results": []},
        )
        self.assertFalse(observation["success"])
        self.assertIn("no executable tool calls", observation["summary"])


class ControllerStateTests(unittest.TestCase):
    def _run_with_decisions(self, decisions, memory_results=None):
        from backend.ciel.core import controller

        memory = Mock()
        memory.recent_conversation.return_value = []
        memory.retrieve_context.return_value = memory_results or []
        memory.evaluate_interaction.return_value = []

        brain = Mock()
        brain.think.side_effect = decisions

        response = Mock()
        response.generate.side_effect = lambda context, decision, stream=True: (
            decision.response or decision.question or "generated"
        )

        with (
            patch.object(controller, "MemoryManager", return_value=memory),
            patch.object(controller, "CIELBrain", return_value=brain),
            patch.object(controller, "ResponseGenerator", return_value=response),
        ):
            result = controller._runController(
                "hello",
                "interaction-test",
                sessionId="session-test",
            )
        return result, memory, brain, response

    def test_complete_ends_without_tools(self):
        result, memory, brain, response = self._run_with_decisions(
            [BrainDecision(state=COMPLETE, response="done")]
        )
        self.assertEqual(result, "done")
        self.assertEqual(brain.think.call_count, 1)
        memory.persist_interaction.assert_called_once()
        memory.evaluate_interaction.assert_called_once()

    def test_need_user_returns_question_without_memory_commit(self):
        result, memory, _, _ = self._run_with_decisions(
            [BrainDecision(state=NEED_USER, question="Which repo?")]
        )
        self.assertEqual(result, "Which repo?")
        memory.persist_interaction.assert_called_once()
        memory.evaluate_interaction.assert_not_called()

    def test_failed_is_persisted_but_not_committed_as_memory(self):
        result, memory, _, _ = self._run_with_decisions(
            [BrainDecision(state=FAILED, response="cannot continue", result={"error": "x"})]
        )
        self.assertEqual(result, "cannot continue")
        memory.persist_interaction.assert_called_once()
        memory.evaluate_interaction.assert_not_called()

    def test_need_memory_with_no_new_results_adds_observation_then_completes(self):
        result, memory, brain, _ = self._run_with_decisions(
            [
                BrainDecision(
                    state=NEED_MEMORY,
                    memory_request={"query": "router history"},
                ),
                BrainDecision(state=COMPLETE, response="done"),
            ],
            memory_results=[],
        )
        self.assertEqual(result, "done")
        self.assertEqual(brain.think.call_count, 2)
        self.assertGreaterEqual(memory.retrieve_context.call_count, 2)


if __name__ == "__main__":
    unittest.main()
