from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InteractionContext:
    interaction_id: str
    session_id: str
    user_message: str
    iteration: int = 0
    status: str = "active"
    conversation_context: list[dict[str, Any]] = field(default_factory=list)
    working_memory: dict[str, Any] = field(default_factory=dict)
    retrieved_memories: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    routed_actions: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    current_plan: list[str] = field(default_factory=list)
    memory_candidates: list[dict[str, Any]] = field(default_factory=list)
    brain_decisions: list[dict[str, Any]] = field(default_factory=list)
    final_response: str | None = None
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    @classmethod
    def create(
        cls,
        user_message: str,
        interaction_id: str,
        session_id: str | None = None,
    ) -> "InteractionContext":
        return cls(
            interaction_id=interaction_id,
            session_id=session_id or "default",
            user_message=user_message,
            working_memory={
                "objective": user_message,
                "temporary_conclusions": [],
                "active_assumptions": [],
            },
        )

    def add_action(self, action: dict[str, Any]) -> None:
        self.actions.append(action)

    def add_observation(self, observation: dict[str, Any]) -> None:
        self.observations.append(observation)

    def add_retrieved_memories(self, memories: list[dict[str, Any]]) -> None:
        seen = {
            (memory.get("scope"), memory.get("id"))
            for memory in self.retrieved_memories
            if memory.get("id") is not None
        }
        for memory in memories:
            key = (memory.get("scope"), memory.get("id"))
            if memory.get("id") is not None and key in seen:
                continue
            self.retrieved_memories.append(memory)
            if memory.get("id") is not None:
                seen.add(key)

    def add_memory_candidates(self, candidates: list[dict[str, Any]]) -> None:
        for candidate in candidates:
            if candidate not in self.memory_candidates:
                self.memory_candidates.append(candidate)

    def finish(self, status: str, response: str | None = None) -> None:
        self.status = status
        if response is not None:
            self.final_response = response
        self.completed_at = time.time()

    def to_record(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "iteration": self.iteration,
            "status": self.status,
            "conversation_context": self.conversation_context,
            "working_memory": self.working_memory,
            "retrieved_memories": self.retrieved_memories,
            "actions": self.actions,
            "routed_actions": self.routed_actions,
            "tool_results": self.tool_results,
            "observations": self.observations,
            "current_plan": self.current_plan,
            "memory_candidates": self.memory_candidates,
            "brain_decisions": self.brain_decisions,
            "final_response": self.final_response,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
