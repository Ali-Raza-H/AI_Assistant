import unittest

from backend.ciel.brain.schemas import (
    ACTION_REQUIRED,
    COMPLETE,
    NEED_MEMORY,
    NEED_USER,
    BrainDecision,
    BrainDecisionValidationError,
)


class BrainDecisionTests(unittest.TestCase):
    def test_valid_complete_decision(self):
        decision = BrainDecision.from_dict(
            {"state": COMPLETE, "response": "done"}
        )
        self.assertEqual(decision.state, COMPLETE)
        self.assertEqual(decision.response, "done")

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"state": "whatever", "response": "x"})

    def test_missing_state_is_rejected(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"response": "x"})

    def test_action_required_needs_action(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"state": ACTION_REQUIRED})

    def test_need_memory_needs_request(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"state": NEED_MEMORY})

    def test_need_user_needs_question(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"state": NEED_USER})

    def test_complete_needs_response_or_result(self):
        with self.assertRaises(BrainDecisionValidationError):
            BrainDecision.from_dict({"state": COMPLETE})


if __name__ == "__main__":
    unittest.main()
