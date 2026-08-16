import json

from src.tools.logger import log
from src.tools.settings import CHAT_HISTORY_PATH

historyJsonPath = CHAT_HISTORY_PATH
file = "chatHistoryTools.py"


def loadChatHistory():
    log("debug", f"{file}: load chat history function started")
    try:
        with open(historyJsonPath, "r", encoding="utf-8") as jsonDataRead:
            chatHistory = json.load(jsonDataRead)
    except (FileNotFoundError, json.JSONDecodeError):
        chatHistory = []

    if not isinstance(chatHistory, list):
        chatHistory = []

    log("info", f"{file}: chat history returning {chatHistory}")
    return chatHistory


def saveChatHistory(userMessage, AIresponse):
    log("debug", f"{file}: save chat history function started")
    jsonData = loadChatHistory()
    jsonData.append(
        {"userMessage": userMessage, "assistantResponse": AIresponse}
    )

    with open(historyJsonPath, "w", encoding="utf-8") as jsonFile:
        json.dump(jsonData, jsonFile, indent=2)
    log("debug", f"{file}: save chat history function finished")


def wipeChatHistory():
    log("debug", f"{file}: wipe chat history function started")
    with open(historyJsonPath, "w", encoding="utf-8") as jsonFile:
        json.dump([], jsonFile)
    log("debug", f"{file}: wipe chat history function finished")
