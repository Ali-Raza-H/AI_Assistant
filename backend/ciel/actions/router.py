from __future__ import annotations

from typing import Any

from backend.ciel.runtime.settings import routerPrompt


class ActionRouter:
    def route(
        self,
        action: dict[str, Any],
        brain_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import json

        from backend.ciel.core.router import routeOnce
        from backend.ciel.core.tool_dispatcher import normalizeRouterInput

        user_input = (
            "BRAIN ACTION:\n"
            f"{json.dumps(action, indent=2)}\n\n"
            "RELEVANT CONTEXT:\n"
            f"{json.dumps(brain_context or {}, indent=2)}"
        )
        return normalizeRouterInput(routeOnce(routerPrompt, user_input))
