from __future__ import annotations

import json
from typing import Any

from backend.ciel.brain.schemas import BrainDecision, COMPLETE
from backend.ciel.providers.manager import ProviderManager
from backend.ciel.runtime.json_repair import fixJson
from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import llmPrompt


FILE = "brain.py"


class CIELBrain:
    def __init__(self, provider_manager: ProviderManager | None = None, provider: str = "gemini"):
        self.provider_manager = provider_manager or ProviderManager()
        self.provider = provider

    def think(self, brain_context: dict[str, Any]) -> BrainDecision:
        system_prompt = (
            f"{llmPrompt}\n"
            "You are operating as CIEL Brain.\n"
            "You are the cognitive authority. Decide the next state, but do not execute tools.\n"
            "Return only a compact JSON object. Do not include hidden chain-of-thought.\n"
        )
        user_prompt = (
            "Decide CIEL's next state from this context.\n\n"
            "Allowed states:\n"
            "- action_required: a tool-backed action is needed.\n"
            "- need_memory: more long-term memory is needed.\n"
            "- need_user: the user must clarify something.\n"
            "- complete: the objective can be answered now.\n"
            "- failed: the objective cannot be completed.\n\n"
            "For action_required, include action with semantic fields such as "
            "intent, target, purpose, and reason.\n"
            "For complete, include response or result.\n"
            "For need_memory, include memory_request with query and scopes.\n"
            "Include plan and memory_candidates only when useful.\n\n"
            f"Brain context:\n{json.dumps(brain_context, indent=2)}"
        )
        log("debug", f"{FILE}: requesting brain decision")
        raw_response = self.provider_manager.complete(
            self.provider,
            system_prompt,
            user_prompt,
            stream=False,
        )
        return self._parse_decision(raw_response)

    def _parse_decision(self, raw_response: str) -> BrainDecision:
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            try:
                parsed = json.loads(fixJson(raw_response))
            except Exception:
                log("error", f"{FILE}: brain returned non-JSON completion")
                return BrainDecision(
                    state=COMPLETE,
                    response=raw_response.strip(),
                    raw={"unparsed": raw_response},
                )
        if not isinstance(parsed, dict):
            return BrainDecision(
                state=COMPLETE,
                response=str(raw_response).strip(),
                raw={"unparsed": raw_response},
            )
        return BrainDecision.from_dict(parsed)
