import json

from backend.ciel.core.tool_dispatcher import normalizeRouterInput, parseRouterInput
from backend.ciel.providers.groq import groqComm
from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import (
    routerPrompt,
    routerSchema,
)

file = "router.py"
maxFormatRetries = 2


def loadRouterHistory():
    log("debug", f"{file}: router history is no longer persisted")
    return []


def saveRouterHistory(routerHistory):
    log("debug", f"{file}: ignoring legacy router history save")


def clearRouterHistory():
    log("debug", f"{file}: router history clear is a no-op")


def routeOnce(systemPrompt, userInput):
    validationError = None

    for attempt in range(maxFormatRetries):
        retryInput = userInput
        if validationError is not None:
            retryInput += (
                "\n\nYour previous response failed validation: "
                f"{validationError}. Return only a JSON object matching the schema."
            )

        routerOutput = groqComm(
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
    if latestContext is not None:
        systemPrompt += (
            "\nLATEST INTERACTION CONTEXT:\n" + json.dumps(latestContext, indent=2)
        )

    userInput = (
        f"BRAIN ACTION OR LEGACY USER INPUT: {userMsg}\n"
        f"Interaction iteration: {iteration}"
    )
    log("debug", f"{file}: requesting action route for iteration {iteration}")
    return routeOnce(systemPrompt, userInput)
