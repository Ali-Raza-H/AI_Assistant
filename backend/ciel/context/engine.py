from __future__ import annotations

from typing import Any

from backend.ciel.context.interaction import InteractionContext
from backend.ciel.memory.manager import MemoryManager
from backend.ciel.runtime.settings import toolDat


class ContextEngine:
    def __init__(self, memory_manager: MemoryManager | None = None):
        self.memory_manager = memory_manager or MemoryManager()

    def prepare_interaction(self, context: InteractionContext) -> None:
        context.conversation_context = self.memory_manager.recent_conversation(
            limit=12,
            session_id=context.session_id,
        )
        context.add_retrieved_memories(
            self.memory_manager.retrieve_context(
                {
                    "query": context.user_message,
                    "session_id": context.session_id,
                    "interaction_id": context.interaction_id,
                }
            )
        )

    def build_brain_context(self, context: InteractionContext) -> dict[str, Any]:
        return {
            "interaction_id": context.interaction_id,
            "session_id": context.session_id,
            "user_message": context.user_message,
            "iteration": context.iteration,
            "status": context.status,
            "conversation_context": context.conversation_context[-12:],
            "working_memory": self._compact_working_memory(context.working_memory),
            "retrieved_memories": context.retrieved_memories[-8:],
            "actions": context.actions[-8:],
            "observations": context.observations[-8:],
            "current_plan": context.current_plan,
            "available_capabilities": toolDat,
        }

    def _compact_working_memory(self, working_memory: dict[str, Any]) -> dict[str, Any]:
        compact = dict(working_memory)
        for key, value in list(compact.items()):
            if isinstance(value, list) and len(value) > 8:
                compact[key] = value[-8:]
        return compact
