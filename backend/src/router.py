import json

from modules.toolManager import normalizeRouterInput, parseRouterInput
from src.providers.ollamaProv import ollamaComm
from src.tools.flagManager import flags
from src.tools.logger import log
from src.tools.settings import ROUTER_HISTORY_PATH, routerPrompt, routerSchema

file = "router.py"
path = ROUTER_HISTORY_PATH
maxFormatRetries = 2


def loadRouterHistory():
    log("debug", f"{file}: load router history function started")
    try:
        with open(path, "r", encoding="utf-8") as routerHistoryData:
            routerHistory = json.load(routerHistoryData)
    except (FileNotFoundError, json.JSONDecodeError):
        routerHistory = []

    if not isinstance(routerHistory, list):
        routerHistory = []

    log("info", f"{file}: router history contains {len(routerHistory)} item(s)")
    return routerHistory


def saveRouterHistory(routerHistory):
    with open(path, "w", encoding="utf-8") as routerHistoryData:
        json.dump(routerHistory, routerHistoryData, indent=2)


def clearRouterHistory():
    saveRouterHistory([])


def routeOnce(systemPrompt, userInput):
    validationError = None

    for attempt in range(maxFormatRetries):
        retryInput = userInput
        if validationError is not None:
            retryInput += (
                "\n\nYour previous response failed validation: "
                f"{validationError}. Return only a JSON object matching the schema."
            )

        routerOutput = ollamaComm(
            systemPrompt,
            retryInput,
            False,
            responseFormat=routerSchema,
        )
        try:
            parsedOutput = parseRouterInput(routerOutput)
            return normalizeRouterInput(parsedOutput)
        except (TypeError, ValueError) as error:
            validationError = error
            log(
                "error",
                f"{file}: invalid router output on attempt {attempt + 1}: {error}",
            )

    raise ValueError(
        f"Router failed to return a valid decision after {maxFormatRetries} attempts: "
        f"{validationError}"
    )


def router(userMsg, latestContext=None, iteration=1):
    systemPrompt = routerPrompt

    if flags.doRemember:
        routerHistory = loadRouterHistory()
        if routerHistory:
            systemPrompt += (
                "\nROUTER HISTORY:\n" + json.dumps(routerHistory, indent=2)
            )
    elif latestContext is not None:
        systemPrompt += (
            "\nLATEST LOOP CONTEXT:\n" + json.dumps(latestContext, indent=2)
        )

    userInput = (
        f"Original user input: {userMsg}\n"
        f"Controller iteration: {iteration}"
    )
    log(
        "debug",
        f"{file}: requesting decision for iteration {iteration}; "
        f"doRemember={flags.doRemember}",
    )
    return routeOnce(systemPrompt, userInput)
