import json

from backend.ciel.core.events import eventBus
from backend.ciel.context.interaction import InteractionContext
from backend.ciel.brain.schemas import BrainDecision, COMPLETE
from backend.ciel.response.generator import ResponseGenerator
from backend.ciel.providers.google import geminiComm
from backend.ciel.runtime.chat_history import loadChatHistory
from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import llmPrompt
from backend.ciel.runtime.speech import speak

file = "ciel.py"


def generateCIELResponse(
    userMessage,
    iteration,
    routerDecision,
    toolExecution,
    interactionId=None,
    isFinal=True,
    priorCycles=None,
):
    chatHistory = loadChatHistory()
    systemPrompt = f"{llmPrompt}\nCHAT HISTORY:\n{json.dumps(chatHistory)}"
    cycleContext = {
        "iteration": iteration,
        "priorCycles": priorCycles or [],
        "routerDecision": routerDecision,
        "effectiveFlags": toolExecution["flags"],
        "toolResults": toolExecution["results"],
    }
    if isFinal:
        responseInstruction = (
            "Give the user one natural, direct answer to their original message. "
            "Use the current tool results as evidence. Do not narrate internal stages, "
            "iterations, routing, or planned retries. If a permission error occurred, "
            "state clearly that the requested access was not allowed."
        )
    else:
        responseInstruction = (
            "Write a concise private controller note, not a message to the user. "
            "State what the current results established and exactly what remains to "
            "satisfy the original request. Do not turn earlier assistant wording into "
            "a new user instruction."
        )
    modelMessage = (
        f"User's original message: {userMessage}\n"
        f"{responseInstruction}\n"
        f"Current controller context:\n{json.dumps(cycleContext, indent=2)}"
    )

    log("debug", f"{file}: generating response for iteration {iteration}")
    eventData = {"interactionId": interactionId, "iteration": iteration}

    def onToken(token):
        eventBus.emit("ciel.token", {**eventData, "token": token})

    fullResponse = geminiComm(
        systemPrompt,
        modelMessage,
        isFinal,
        onToken=onToken if isFinal else None,
    )
    if isFinal:
        eventBus.emit("speech.started", eventData)
        speak(fullResponse)
        eventBus.emit("speech.ended", eventData)
    return fullResponse


def generateFinalResponse(context: InteractionContext, decision: BrainDecision):
    return ResponseGenerator().generate(context, decision)


def generateFallbackResponse(context: InteractionContext, message: str):
    decision = BrainDecision(state=COMPLETE, response=message)
    return ResponseGenerator().generate(context, decision)
