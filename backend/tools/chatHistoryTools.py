import json
import time


historyJsonPath = 'backend/schemas/chatHistory.json'
jsonData = []

def loadChatHistory():
    with open(historyJsonPath, 'r') as jsonDataRead:
        chatHistory = json.load(jsonDataRead)
        jsonData.append(chatHistory)
        print("chatHistoryTools file:")
        print("load chat history funciton used")
        time.sleep(3)
    return jsonData

def saveChatHistory(userMessage, AIresponse):
    chatHistory = {
        "userMessage": userMessage,
        "assistantResponse": AIresponse
    }
    jsonData.append(chatHistory)
    with open(historyJsonPath, 'w') as jsonFile:
        json.dump(jsonData, jsonFile)
    print("chatHistoryTools file:")
    print("Save chat history function used")
    time.sleep(3)


def wipeChatHistory():
    with open(historyJsonPath, 'w') as jsonFile:
        json.dump([], jsonFile)
    print("chatHistoryTools file:")
    print("Wipe chat history funciton used")
    time.sleep(3)