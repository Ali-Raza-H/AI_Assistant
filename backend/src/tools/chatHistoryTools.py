import json

from src.tools.logger import log
from src.tools.settings import CHAT_HISTORY_PATH

historyJsonPath = CHAT_HISTORY_PATH
file = "chatHistoryTools.py:"
jsonData = []


def loadChatHistory():
    log("debug", f"{file} load chat history function started")

    with open(historyJsonPath, "r") as jsonDataRead:
        chatHistory = json.load(jsonDataRead)
        # jsonData.append(chatHistory)
        log("debug", f"{file} load chat history function finished")
        log("info", f"{file} Chat history return {jsonData}")

    return jsonData


def saveChatHistory(userMessage, AIresponse):
    log("debug", f"{file} save chat history function started")

    chatHistory = {"userMessage": userMessage, "assistantResponse": AIresponse}

    log("info", f"P{file} Data to be saved {chatHistory}")
    jsonData.append(chatHistory)
    with open(historyJsonPath, "w") as jsonFile:
        json.dump(jsonData, jsonFile)
    log("debug", f"{file} save chat history function finished")


def wipeChatHistory():
    log("debug", f"{file} wipe chat history function started")
    with open(historyJsonPath, "w") as jsonFile:
        json.dump([], jsonFile)
    log("debug", f"{file}, wipe chat history function finished")
