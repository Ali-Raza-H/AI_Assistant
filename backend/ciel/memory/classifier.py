from __future__ import annotations

from typing import Any

from backend.ciel.context.interaction import InteractionContext


class MemoryClassifier:
    def classify(self, context: InteractionContext) -> list[dict[str, Any]]:
        candidates = list(context.memory_candidates)
        if self._should_create_episode(context):
            candidates.append(
                {
                    "type": "episode_candidate",
                    "summary": self._episode_summary(context),
                    "source": "completed_interaction",
                    "importance": self._episode_importance(context),
                    "topics": self._topics(context),
                }
            )
        return candidates

    def _should_create_episode(self, context: InteractionContext) -> bool:
        if context.status != "complete" or not context.final_response:
            return False
        if context.memory_candidates:
            return False
        message = context.user_message.strip()
        if len(message.split()) < 6 and not context.actions and not context.observations:
            return False
        durable_markers = (
            "remember",
            "preference",
            "prefer",
            "project",
            "fixed",
            "changed",
            "decision",
            "bug",
            "architecture",
            "router",
            "memory",
            "lifeos",
            "ciel",
        )
        lowered = f"{message} {context.final_response}".lower()
        return bool(context.actions or context.observations or any(marker in lowered for marker in durable_markers))

    def _episode_summary(self, context: InteractionContext) -> str:
        result = (context.final_response or "").strip()
        if len(result) > 500:
            result = result[:500].rstrip() + "..."
        return f"User asked: {context.user_message.strip()}\nOutcome: {result}"

    def _episode_importance(self, context: InteractionContext) -> float:
        if context.actions or context.observations:
            return 0.65
        return 0.45

    def _topics(self, context: InteractionContext) -> list[str]:
        text = f"{context.user_message} {context.final_response or ''}".lower()
        known_topics = ["ciel", "router", "memory", "lifeos", "project", "bug", "architecture"]
        return [topic for topic in known_topics if topic in text]
