from __future__ import annotations

from typing import Callable

from backend.ciel.providers.google import geminiComm
from backend.ciel.providers.groq import groqComm


class ProviderManager:
    def complete(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        stream: bool = False,
        response_format: dict | str | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        provider_name = provider.strip().lower()
        if provider_name in {"gemini", "google", "ciel"}:
            return geminiComm(system_prompt, user_prompt, stream, onToken=on_token)
        if provider_name == "groq":
            return groqComm(
                system_prompt,
                user_prompt,
                stream,
                responseFormat=response_format,
            )
        raise ValueError(f"Unknown provider: {provider}")
