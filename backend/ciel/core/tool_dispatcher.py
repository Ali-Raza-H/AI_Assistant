import json

from backend.ciel.agent_tools.lifeos.client import (
    LIFEOS_OPERATIONS,
    isLifeOSPermissionError,
    runLifeOSAction,
)
from backend.ciel.agent_tools.shell import runCommands
from backend.ciel.core.events import eventBus
from backend.ciel.runtime.flags import flags
from backend.ciel.runtime.json_repair import fixJson
from backend.ciel.runtime.logging import log

file = "toolManager.py"
allowedTools = {"runBash", "lifeOS"}


def parseRouterInput(routerInput):
    if isinstance(routerInput, dict):
        return routerInput
    if not isinstance(routerInput, str):
        raise TypeError("Router output must be a JSON string or dictionary")

    try:
        return json.loads(routerInput)
    except json.JSONDecodeError:
        log("error", f"{file}: router returned invalid JSON")
        try:
            return json.loads(fixJson(routerInput))
        except (ValueError, SyntaxError, json.JSONDecodeError) as error:
            raise ValueError("Router output could not be parsed as JSON") from error


def normalizeRouterInput(routerInput):
    if not isinstance(routerInput, dict):
        raise ValueError("Router output must contain a JSON object")

    # Temporary compatibility with the previous {tool, action} contract.
    if "tool" in routerInput:
        toolName = routerInput.get("tool")
        hasTool = toolName not in {None, "None"}
        routerInput = {
            "flags": {
                "isLooping": hasTool,
                "doRemember": hasTool,
            },
            "tools": (
                [
                    {
                        "tool": toolName,
                        "action": routerInput.get("action", ""),
                        "arguments": routerInput.get("arguments", {}),
                    }
                ]
                if hasTool
                else []
            ),
        }

    routerFlags = routerInput.get("flags")
    tools = routerInput.get("tools")
    if not isinstance(routerFlags, dict):
        raise ValueError("Router output is missing the flags object")
    if not isinstance(tools, list):
        raise ValueError("Router output is missing the tools list")

    normalizedFlags = {
        "isLooping": routerFlags.get("isLooping"),
        "doRemember": routerFlags.get("doRemember"),
    }
    for flagName, state in normalizedFlags.items():
        if type(state) is not bool:
            raise ValueError(f"Router flag {flagName} must be a boolean")

    normalizedTools = []
    for tool in tools:
        if not isinstance(tool, dict):
            raise ValueError("Every tool entry must be an object")
        toolName = tool.get("tool")
        action = tool.get("action")
        arguments = tool.get("arguments", {})
        if toolName not in allowedTools:
            raise ValueError(f"Unknown router tool: {toolName}")
        if not isinstance(action, str) or not action.strip():
            raise ValueError(f"Tool {toolName} requires a non-empty action")
        if not isinstance(arguments, dict):
            raise ValueError(f"Tool {toolName} arguments must be an object")
        if toolName == "runBash" and arguments:
            raise ValueError("runBash arguments must be an empty object")
        if toolName == "lifeOS" and action not in LIFEOS_OPERATIONS:
            raise ValueError(f"Unknown LifeOS operation: {action}")
        normalizedTools.append(
            {"tool": toolName, "action": action, "arguments": arguments}
        )

    return {"flags": normalizedFlags, "tools": normalizedTools}


def executeToolCalls(routerInput, interactionId=None, iteration=None):
    log("debug", f"{file}: execute tool calls function started")
    inputJson = normalizeRouterInput(parseRouterInput(routerInput))
    selectedTools = [
        {"tool": tool["tool"], "action": tool["action"]}
        for tool in inputJson["tools"]
    ]
    log("info", f"{file}: selected tools: {selectedTools}")

    results = []
    for toolIndex, tool in enumerate(inputJson["tools"]):
        log("info", f"{file}: running {tool['tool']}/{tool['action']}")
        eventBus.emit(
            "tool.started",
            {
                "interactionId": interactionId,
                "iteration": iteration,
                "index": toolIndex,
                "tool": tool,
            },
        )
        try:
            if tool["tool"] == "lifeOS":
                commandResult = runLifeOSAction(tool["action"], tool["arguments"])
            else:
                commandResult = runCommands(tool["action"])
        except Exception as error:
            log(
                "error",
                f"{file}: {tool['tool']}/{tool['action']} raised an error: {error}",
            )
            commandResult = {
                "success": False,
                "error": str(error),
            }
        toolResult = {
            "tool": tool["tool"],
            "action": tool["action"],
            **commandResult,
        }
        results.append(toolResult)
        eventBus.emit(
            "tool.completed",
            {
                "interactionId": interactionId,
                "iteration": iteration,
                "index": toolIndex,
                "result": toolResult,
            },
        )

    return {
        "flags": dict(inputJson["flags"]),
        "tools": inputJson["tools"],
        "results": results,
    }


def toolRouter(routerInput, interactionId=None, iteration=None):
    log("debug", f"{file}: legacy tool router function started")

    toolExecution = executeToolCalls(
        routerInput,
        interactionId=interactionId,
        iteration=iteration,
    )
    effectiveFlags = dict(toolExecution["flags"])
    for flagName, state in effectiveFlags.items():
        flags.setFlagState(flagName, state)

    results = toolExecution["results"]
    failedResults = [result for result in results if result.get("success") is not True]
    permissionFailures = [
        result
        for result in failedResults
        if result.get("tool") == "lifeOS" and isLifeOSPermissionError(result)
    ]
    retryableFailures = [
        result
        for result in failedResults
        if not (
            result.get("tool") == "lifeOS" and isLifeOSPermissionError(result)
        )
    ]

    if retryableFailures:
        effectiveFlags = {"isLooping": True, "doRemember": True}
        flags.setFlagState("isLooping", True)
        flags.setFlagState("doRemember", True)
        log("info", f"{file}: tool failure forced both controller flags to true")
    elif permissionFailures:
        effectiveFlags = {"isLooping": False, "doRemember": False}
        flags.setFlagState("isLooping", False)
        flags.setFlagState("doRemember", False)
        log("info", f"{file}: LifeOS permission denial ended the controller loop")

    return {
        **toolExecution,
        "flags": effectiveFlags,
    }
