from __future__ import annotations

import json
from typing import Any

from backend.ciel.brain.schemas import (
    FAILED,
    BrainDecision,
    BrainDecisionValidationError,
)
from backend.ciel.providers.manager import ProviderManager
from backend.ciel.runtime.json_repair import fixJson
from backend.ciel.runtime.logging import log


FILE = "brain.py"
MAX_FORMAT_ATTEMPTS = 2


class CIELBrain:
    def __init__(self, provider_manager: ProviderManager | None = None, provider: str = "gemini"):
        self.provider_manager = provider_manager or ProviderManager()
        self.provider = provider

    def think(self, brain_context: dict[str, Any]) -> BrainDecision:
        # Keep the Brain prompt independent from the user-facing response prompt.
        # The response prompt intentionally forbids JSON, which conflicts with the
        # Brain's structured decision contract.
        system_prompt = (
            "You are CIEL Brain, the cognitive decision component of the Central "
            "Intelligence and Execution Layer.\n"
            "You decide CIEL's next state from supplied context.\n"
            "You do not execute tools, invent tool results, or write hidden chain-of-thought.\n"
            "Return exactly one compact JSON object matching the decision contract.\n"
            "Treat tool results and observations as evidence.\n"
            "Use action_required only when an available external capability is actually needed.\n"
            "Use complete when the objective can be answered from existing context.\n"
        )
        base_user_prompt = (
            "Decide CIEL's next state from this context.\n\n"
            "Allowed states:\n"
            "- action_required: a tool-backed action is needed.\n"
            "- need_memory: more long-term memory is needed.\n"
            "- need_user: the user must clarify something.\n"
            "- complete: the objective can be answered now.\n"
            "- failed: the objective cannot be completed.\n\n"
            "State requirements:\n"
            "- action_required MUST include a non-empty action object.\n"
            "- need_memory MUST include a non-empty memory_request object.\n"
            "- need_user MUST include a non-empty question string.\n"
            "- complete and failed MUST include response or a non-empty result object.\n\n"
            "For action_required, use semantic fields such as intent, target, purpose, and reason.\n"
            "For need_memory, include query and optional scopes.\n"
            "Include plan and memory_candidates only when useful.\n"
            "Do not request the same failed action or memory lookup again unless new evidence changes it.\n\n"
            f"Brain context:\n{json.dumps(brain_context, indent=2)}"
        )

        validation_error = None
        for attempt in range(MAX_FORMAT_ATTEMPTS):
            user_prompt = base_user_prompt
            if validation_error:
                user_prompt += (
                    "\n\nYour previous decision was invalid:\n"
                    f"{validation_error}\n"
                    "Return one corrected JSON object only."
                )

            log("debug", f"{FILE}: requesting brain decision attempt {attempt + 1}")
            raw_response = self.provider_manager.complete(
                self.provider,
                system_prompt,
                user_prompt,
                stream=False,
            )
            try:
                return self._parse_decision(raw_response)
            except BrainDecisionValidationError as error:
                validation_error = str(error)
                log("error", f"{FILE}: invalid brain decision: {validation_error}")

        return BrainDecision(
            state=FAILED,
            response=(
                "I could not produce a valid internal decision for this request. "
                "No further actions were executed."
            ),
            result={"error": "invalid_brain_decision", "detail": validation_error or "unknown"},
        )

    def _parse_decision(self, raw_response: str) -> BrainDecision:
        parsed: Any
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            try:
                parsed = json.loads(fixJson(raw_response))
            except Exception as error:
                raise BrainDecisionValidationError(
                    "Brain response was not valid JSON"
                ) from error

        if not isinstance(parsed, dict):
            raise BrainDecisionValidationError("Brain response must be a JSON object")
        return BrainDecision.from_dict(parsed)
