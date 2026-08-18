from __future__ import annotations

import json

from backend.ciel.brain.schemas import BrainDecision
from backend.ciel.context.interaction import InteractionContext
from backend.ciel.core.events import eventBus
from backend.ciel.providers.manager import ProviderManager
from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import llmPrompt
from backend.ciel.runtime.speech import speak


FILE = "response_generator.py"


class ResponseGenerator:
    def __init__(
        self,
        provider_manager: ProviderManager | None = None,
        provider: str = "gemini",
    ):
        self.provider_manager = provider_manager or ProviderManager()
        self.provider = provider

    def generate(
        self,
        context: InteractionContext,
        decision: BrainDecision,
        stream: bool = True,
    ) -> str:
        event_data = {
            "interactionId": context.interaction_id,
            "iteration": context.iteration,
        }
        eventBus.emit("response.started", event_data)

        if decision.response and decision.state in {"complete", "need_user", "failed"}:
            response = decision.response
            if stream:
                eventBus.emit("response.token", {**event_data, "token": response})
        elif decision.question:
            response = decision.question
            if stream:
                eventBus.emit("response.token", {**event_data, "token": response})
        else:
            response = self._generate_from_context(context, decision, stream)

        eventBus.emit("response.completed", {**event_data, "response": response})
        self._speak_best_effort(response, event_data)
        return response

    def _generate_from_context(
        self,
        context: InteractionContext,
        decision: BrainDecision,
        stream: bool,
    ) -> str:
        log("debug", f"{FILE}: generating final response")
        event_data = {
            "interactionId": context.interaction_id,
            "iteration": context.iteration,
        }

        def on_token(token: str) -> None:
            eventBus.emit("response.token", {**event_data, "token": token})

        prompt = (
            "Generate one concise user-facing response for the completed interaction.\n"
            "Do not expose hidden reasoning, JSON, routing details, or internal flags.\n"
            "Use observations as evidence and be explicit about failures or permission denials.\n\n"
            f"User message: {context.user_message}\n"
            f"Decision: {json.dumps(decision.to_dict(), indent=2)}\n"
            f"Observations: {json.dumps(context.observations[-8:], indent=2)}"
        )
        return self.provider_manager.complete(
            self.provider,
            llmPrompt,
            prompt,
            stream=stream,
            on_token=on_token if stream else None,
        )

    def _speak_best_effort(self, response: str, event_data: dict) -> None:
        eventBus.emit("speech.started", event_data)
        try:
            speak(response)
        except Exception as error:
            log("error", f"{FILE}: speech failed after response generation: {error}")
            eventBus.emit(
                "speech.failed",
                {**event_data, "error": str(error)},
            )
            return
        eventBus.emit("speech.ended", event_data)
