import json

from src.providers.googleProv import geminiComm
from src.events import eventBus
from src.tools.chatHistoryTools import loadChatHistory
from src.tools.logger import log
from src.tools.settings import llmPrompt
from src.tools.ttsEngine import speak

file = "ciel.py"


def generateCIELResponse(
    userMessage,
    iteration,
    routerDecision,
    toolExecution,
    interactionId=None,
):
    chatHistory = loadChatHistory()
    systemPrompt = f"{llmPrompt}\nCHAT HISTORY:\n{json.dumps(chatHistory)}"
    cycleContext = {
        "iteration": iteration,
        "routerDecision": routerDecision,
        "effectiveFlags": toolExecution["flags"],
        "toolResults": toolExecution["results"],
    }
    modelMessage = (
        f"User's message: {userMessage}\n"
        "This response will be shown and spoken to the user. Clearly explain "
        "what has happened in the current stage and what is happening next.\n"
        f"Current controller context:\n{json.dumps(cycleContext, indent=2)}"
    )

    log("debug", f"{file}: generating response for iteration {iteration}")
    eventData = {"interactionId": interactionId, "iteration": iteration}

    def onToken(token):
        eventBus.emit("ciel.token", {**eventData, "token": token})

    fullResponse = geminiComm(systemPrompt, modelMessage, True, onToken=onToken)
    eventBus.emit("speech.started", eventData)
    speak(fullResponse)
    eventBus.emit("speech.ended", eventData)
    return fullResponse
