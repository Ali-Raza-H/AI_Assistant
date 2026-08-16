import threading
import uuid

from modules.toolManager import toolRouter
from src.ciel import generateCIELResponse
from src.events import eventBus
from src.router import clearRouterHistory, loadRouterHistory, router, saveRouterHistory
from src.tools.chatHistoryTools import saveChatHistory
from src.tools.flagManager import flags
from src.tools.logger import log

file = "controller.py"

# Emergency guard only. The router flags control normal loop termination.
maxControllerIterations = 5
_controllerLock = threading.Lock()


def isControllerBusy():
    return _controllerLock.locked()


def runController(userMessage, interactionId=None):
    interactionId = interactionId or uuid.uuid4().hex
    with _controllerLock:
        return _runController(userMessage, interactionId)


def _runController(userMessage, interactionId):
    flags.setFlagState("isLooping", True)
    flags.setFlagState("doRemember", True)
    eventBus.emit(
        "interaction.started",
        {"interactionId": interactionId, "message": userMessage},
    )

    latestContext = None
    latestResponse = None

    try:
        for iteration in range(1, maxControllerIterations + 1):
            log("debug", f"{file}: starting iteration {iteration}")
            eventData = {"interactionId": interactionId, "iteration": iteration}
            eventBus.emit(
                "router.started",
                {
                    **eventData,
                    "contextMode": "history" if flags.doRemember else "latest",
                },
            )

            routerDecision = router(
                userMessage,
                latestContext=latestContext,
                iteration=iteration,
            )
            eventBus.emit(
                "router.decision", {**eventData, "decision": routerDecision}
            )
            eventBus.emit(
                "tools.started",
                {**eventData, "tools": routerDecision.get("tools", [])},
            )
            toolExecution = toolRouter(
                routerDecision,
                interactionId=interactionId,
                iteration=iteration,
            )
            eventBus.emit(
                "flags.updated", {**eventData, "flags": toolExecution["flags"]}
            )

            eventBus.emit("ciel.started", eventData)
            cielResponse = generateCIELResponse(
                userMessage=userMessage,
                iteration=iteration,
                routerDecision=routerDecision,
                toolExecution=toolExecution,
                interactionId=interactionId,
            )
            eventBus.emit(
                "ciel.completed", {**eventData, "response": cielResponse}
            )

            # Every CIEL response is user-visible and belongs in chat history.
            saveChatHistory(userMessage, cielResponse)
            eventBus.emit("history.saved", eventData)

            cycleRecord = {
                "iteration": iteration,
                "routerDecision": routerDecision,
                "toolExecution": toolExecution,
                "cielOutput": cielResponse,
            }
            latestContext = cycleRecord
            latestResponse = cielResponse

            if flags.doRemember:
                routerHistory = loadRouterHistory()
                routerHistory.append(cycleRecord)
                saveRouterHistory(routerHistory)

            if not flags.isLooping:
                clearRouterHistory()
                log("info", f"{file}: interaction completed after {iteration} iteration(s)")
                eventBus.emit(
                    "interaction.completed",
                    {**eventData, "response": latestResponse},
                )
                return latestResponse

        flags.setFlagState("isLooping", False)
        flags.setFlagState("doRemember", False)
        clearRouterHistory()
        log(
            "error",
            f"{file}: stopped at the {maxControllerIterations}-iteration safety limit",
        )
        eventBus.emit(
            "interaction.completed",
            {
                "interactionId": interactionId,
                "iteration": maxControllerIterations,
                "response": latestResponse,
                "safetyLimitReached": True,
            },
        )
        return latestResponse
    except Exception as error:
        eventBus.emit(
            "interaction.failed",
            {"interactionId": interactionId, "error": str(error)},
        )
        raise
