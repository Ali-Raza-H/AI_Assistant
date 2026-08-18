from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ACTION_REQUIRED = "action_required"
NEED_MEMORY = "need_memory"
NEED_USER = "need_user"
COMPLETE = "complete"
FAILED = "failed"
VALID_STATES = {ACTION_REQUIRED, NEED_MEMORY, NEED_USER, COMPLETE, FAILED}


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
        state = str(data.get("state") or COMPLETE).strip().lower()
        if state not in VALID_STATES:
            state = COMPLETE
        plan = data.get("plan") or data.get("current_plan") or []
        if isinstance(plan, str):
            plan = [plan]
        if not isinstance(plan, list):
            plan = []
        memory_candidates = data.get("memory_candidates") or []
        if not isinstance(memory_candidates, list):
            memory_candidates = []
        result = data.get("result") or {}
        if not isinstance(result, dict):
            result = {"value": result}
        return cls(
            state=state,
            action=data.get("action") if isinstance(data.get("action"), dict) else None,
            memory_request=(
                data.get("memory_request")
                if isinstance(data.get("memory_request"), dict)
                else None
            ),
            question=data.get("question") if isinstance(data.get("question"), str) else None,
            response=data.get("response") if isinstance(data.get("response"), str) else None,
            result=result,
            plan=plan,
            memory_candidates=memory_candidates,
            raw=data,
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
