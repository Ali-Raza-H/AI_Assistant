import json


historyJsonPath = 'backend/data/chatHistory.json'
jsonData = []

def loadChatHistory():
    with open(historyJsonPath, 'r') as jsonDataRead:
        chatHistory = json.load(jsonDataRead)
        jsonData.append(chatHistory)
    return jsonData

def saveChatHistory(userMessage, AIresponse):
    chatHistory = {
        "userMessage": userMessage,
        "assistantResponse": AIresponse
    }
    jsonData.append(chatHistory)
    with open(historyJsonPath, 'w') as jsonFile:
        json.dump(jsonData, jsonFile)


def wipeChatHistory():
    with open(historyJsonPath, 'w') as jsonFile:
        json.dump([], jsonFile)
