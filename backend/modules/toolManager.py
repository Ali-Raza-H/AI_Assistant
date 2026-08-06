"""Tool orchestration for normalized router output."""

from __future__ import annotations

import json
from typing import Any

from modules.runBashCommands import runCommands
from src.tools.jsonTools import parse_json_response
from src.tools.logger import log
from src.tools.settings import COMMANDS_PATH


def _tool_requests(router_output: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ordered tool requests from both current and legacy contracts."""

    if "tool" in router_output:
        return [
            {
                "tool": router_output.get("tool"),
                "action": router_output.get("action", ""),
            }
        ]

    tools = router_output.get("tools", [])
    if isinstance(tools, dict):
        requests: list[dict[str, Any]] = []
        for tool_name, actions in tools.items():
            if not isinstance(actions, list):
                actions = [actions]
            requests.extend(
                {"tool": tool_name, "action": action} for action in actions
            )
        return requests

    if not isinstance(tools, list):
        return []
    return [tool for tool in tools if isinstance(tool, dict)]


def _save_router_output(router_output: dict[str, Any]) -> None:
    with open(COMMANDS_PATH, "w", encoding="utf-8") as data_file:
        json.dump(router_output, data_file, indent=2)


def execute_tools(router_output: dict[str, Any]) -> list[dict[str, Any]]:
    """Execute tools in the exact order selected by the router."""

    log("debug", "toolManager.py: orchestrator started")
    _save_router_output(router_output)
    results: list[dict[str, Any]] = []

    for request in _tool_requests(router_output):
        tool_name = request.get("tool")
        action = request.get("action", "")

        if tool_name == "llmCom":
            # llmCom is a routing decision, not an executable tool.
            continue

        if tool_name != "runBash":
            results.append(
                {
                    "tool": tool_name,
                    "action": action,
                    "success": False,
                    "result": f"Unknown tool: {tool_name}",
                }
            )
            continue

        result = runCommands(action)
        results.append(
            {
                "tool": tool_name,
                "action": action,
                "success": result["success"],
                "result": result["output"],
                "returnCode": result["returnCode"],
            }
        )

    log("info", f"toolManager.py: collected tool results {results}")
    return results


def toolRouter(routerInput: Any) -> Any:
    """Compatibility wrapper for callers using the former toolRouter API."""

    router_output = parse_json_response(routerInput)
    if not isinstance(router_output, dict):
        raise ValueError("Router output must be a JSON object")

    if router_output.get("tool") == "llmCom":
        return router_output.get("action", "")

    results = execute_tools(router_output)
    if "tool" in router_output and len(results) == 1:
        return results[0]["result"]
    return results
