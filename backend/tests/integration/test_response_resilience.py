import unittest
from unittest.mock import Mock, patch

from backend.ciel.brain.schemas import COMPLETE, BrainDecision
from backend.ciel.context.interaction import InteractionContext
from backend.ciel.response.generator import ResponseGenerator


class ResponseResilienceTests(unittest.TestCase):
    def test_speech_failure_does_not_lose_generated_response(self):
        context = InteractionContext.create("hello", "interaction-1", "session-1")
        context.iteration = 1
        generator = ResponseGenerator(provider_manager=Mock())
        decision = BrainDecision(state=COMPLETE, response="final answer")

        with patch("backend.ciel.response.generator.speak", side_effect=RuntimeError("audio unavailable")):
            response = generator.generate(context, decision, stream=False)

        self.assertEqual(response, "final answer")


if __name__ == "__main__":
    unittest.main()
