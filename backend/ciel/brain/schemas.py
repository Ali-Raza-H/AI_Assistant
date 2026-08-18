from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ACTION_REQUIRED = "action_required"
NEED_MEMORY = "need_memory"
NEED_USER = "need_user"
COMPLETE = "complete"
FAILED = "failed"
VALID_STATES = {ACTION_REQUIRED, NEED_MEMORY, NEED_USER, COMPLETE, FAILED}


class BrainDecisionValidationError(ValueError):
    pass


@dataclass
class BrainDecision:
    state: str
    action: dict[str, Any] | None = None
    memory_request: dict[str, Any] | None = None
    question: str | None = None
    response: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    plan: list[str] = field(default_factory=list)
    memory_candidates: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BrainDecision":
        if not isinstance(data, dict):
            raise BrainDecisionValidationError("Brain decision must be a JSON object")

        raw_state = data.get("state")
        if not isinstance(raw_state, str) or not raw_state.strip():
            raise BrainDecisionValidationError("Brain decision requires a non-empty state")
        state = raw_state.strip().lower()
        if state not in VALID_STATES:
            raise BrainDecisionValidationError(f"Unknown brain state: {state}")

        action = data.get("action") if isinstance(data.get("action"), dict) else None
        memory_request = (
            data.get("memory_request")
            if isinstance(data.get("memory_request"), dict)
            else None
        )
        question = data.get("question") if isinstance(data.get("question"), str) else None
        response = data.get("response") if isinstance(data.get("response"), str) else None

        plan = data.get("plan") or data.get("current_plan") or []
        if isinstance(plan, str):
            plan = [plan]
        if not isinstance(plan, list) or not all(isinstance(item, str) for item in plan):
            raise BrainDecisionValidationError("Brain plan must be a list of strings")

        memory_candidates = data.get("memory_candidates") or []
        if not isinstance(memory_candidates, list) or not all(
            isinstance(item, dict) for item in memory_candidates
        ):
            raise BrainDecisionValidationError(
                "memory_candidates must be a list of objects"
            )

        result = data.get("result") or {}
        if not isinstance(result, dict):
            result = {"value": result}

        if state == ACTION_REQUIRED and not action:
            raise BrainDecisionValidationError(
                "action_required decisions require an action object"
            )
        if state == NEED_MEMORY and not memory_request:
            raise BrainDecisionValidationError(
                "need_memory decisions require a memory_request object"
            )
        if state == NEED_USER and not (question and question.strip()):
            raise BrainDecisionValidationError(
                "need_user decisions require a non-empty question"
            )
        if state in {COMPLETE, FAILED} and not (
            (response and response.strip()) or result
        ):
            raise BrainDecisionValidationError(
                f"{state} decisions require a response or non-empty result"
            )

        return cls(
            state=state,
            action=action,
            memory_request=memory_request,
            question=question,
            response=response,
            result=result,
            plan=plan,
            memory_candidates=memory_candidates,
            raw=dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action,
            "memory_request": self.memory_request,
            "question": self.question,
            "response": self.response,
            "result": self.result,
            "plan": self.plan,
            "memory_candidates": self.memory_candidates,
        }
