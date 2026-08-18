from __future__ import annotations

from typing import Any

from backend.ciel.context.interaction import InteractionContext


SUPPORTED_TYPES = {
    "episode",
    "episode_candidate",
    "fact",
    "semantic_fact",
    "project_fact",
    "preference",
    "entity",
    "relationship",
    "procedure",
}


class MemoryClassifier:
    def classify(self, context: InteractionContext) -> list[dict[str, Any]]:
        candidates = []
        seen = set()

        for raw_candidate in context.memory_candidates:
            candidate = self._normalise_candidate(raw_candidate)
            if candidate is None:
                continue
            key = self._candidate_key(candidate)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(candidate)

        # If the Brain already supplied durable candidates, do not also create a
        # generic episode unless the interaction itself involved meaningful action.
        if self._should_create_episode(context, has_candidates=bool(candidates)):
            episode = {
                "type": "episode_candidate",
                "summary": self._episode_summary(context),
                "source": "completed_interaction",
                "importance": self._episode_importance(context),
                "topics": self._topics(context),
            }
            key = self._candidate_key(episode)
            if key not in seen:
                candidates.append(episode)

        return candidates

    def _normalise_candidate(
        self,
        candidate: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not isinstance(candidate, dict):
            return None
        memory_type = str(candidate.get("type") or "").strip().lower()
        if memory_type not in SUPPORTED_TYPES:
            return None

        normalised = dict(candidate)
        normalised["type"] = memory_type

        if "confidence" in normalised:
            try:
                normalised["confidence"] = min(
                    1.0,
                    max(0.0, float(normalised["confidence"])),
                )
            except (TypeError, ValueError):
                normalised["confidence"] = 0.5
        if "importance" in normalised:
            try:
                normalised["importance"] = min(
                    1.0,
                    max(0.0, float(normalised["importance"])),
                )
            except (TypeError, ValueError):
                normalised["importance"] = 0.5

        if memory_type in {"episode", "episode_candidate"}:
            summary = normalised.get("summary") or normalised.get("description")
            if not isinstance(summary, str) or not summary.strip():
                return None
        elif memory_type in {"fact", "semantic_fact", "project_fact", "preference"}:
            required = ("subject", "predicate")
            if any(not str(normalised.get(field) or "").strip() for field in required):
                return None
            object_value = normalised.get("object") or normalised.get("object_value")
            if not str(object_value or "").strip():
                return None
        elif memory_type == "entity":
            if not str(normalised.get("name") or "").strip():
                return None
        elif memory_type == "relationship":
            if not all(
                str(normalised.get(field) or "").strip()
                for field in ("source_entity_id", "relation", "target_entity_id")
            ):
                return None
        elif memory_type == "procedure":
            if not str(normalised.get("name") or "").strip():
                return None
            steps = normalised.get("steps")
            if steps is not None and not isinstance(steps, list):
                return None

        return normalised

    def _candidate_key(self, candidate: dict[str, Any]) -> tuple:
        memory_type = candidate.get("type")
        if memory_type in {"fact", "semantic_fact", "project_fact", "preference"}:
            return (
                memory_type,
                str(candidate.get("subject") or "").strip().lower(),
                str(candidate.get("predicate") or "").strip().lower(),
                str(candidate.get("object") or candidate.get("object_value") or "")
                .strip()
                .lower(),
            )
        if memory_type in {"episode", "episode_candidate"}:
            return (memory_type, str(candidate.get("summary") or "").strip().lower())
        return (memory_type, repr(sorted(candidate.items(), key=lambda item: item[0])))

    def _should_create_episode(
        self,
        context: InteractionContext,
        has_candidates: bool,
    ) -> bool:
        if context.status != "complete" or not context.final_response:
            return False
        message = context.user_message.strip()
        if len(message.split()) < 6 and not context.actions and not context.observations:
            return False
        if has_candidates and not context.actions and not context.observations:
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
        return bool(
            context.actions
            or context.observations
            or any(marker in lowered for marker in durable_markers)
        )

    def _episode_summary(self, context: InteractionContext) -> str:
        result = (context.final_response or "").strip()
        if len(result) > 500:
            result = result[:500].rstrip() + "..."
        observation_summaries = [
            str(observation.get("summary") or "").strip()
            for observation in context.observations[-3:]
            if str(observation.get("summary") or "").strip()
        ]
        parts = [f"User asked: {context.user_message.strip()}"]
        if observation_summaries:
            parts.append("Observed: " + " | ".join(observation_summaries))
        parts.append(f"Outcome: {result}")
        return "\n".join(parts)

    def _episode_importance(self, context: InteractionContext) -> float:
        if context.actions or context.observations:
            return 0.65
        return 0.45

    def _topics(self, context: InteractionContext) -> list[str]:
        text = f"{context.user_message} {context.final_response or ''}".lower()
        known_topics = [
            "ciel",
            "router",
            "memory",
            "lifeos",
            "project",
            "bug",
            "architecture",
        ]
        return [topic for topic in known_topics if topic in text]
