import ollama
import json
import datetime
import time
from tools.chatHistoryTools import *
from tools.runBashCommands import *
from tools.toolManager import *
from tools.chatHistoryTools import *
from llm.prompts import *
#Variables
chatHistory = loadChatHistory()
dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("backend/schemas/toolsSchema.json", "r") as f:
    tools = "Tools available: ", json.load(f)

#routerPrompt = "DECIDE WHAT TO DO. RESPOND ONLY IN JSON FORMAT. JSON SCHEMA RESPONSE: {'tool': 'tool from tools available', 'action': 'action/response'} Example response: {'tool': 'runBash', 'action': 'ls'}. Available tools: " + str(tools) + "Use llmComs for normal talking and runBash for commands only. You're a router. You're job is not to respond but to route"

newRouterPrompt = routerPrompt

systemPrompt = "You are a helpful assistant that answer questions and calls tools available as needed " + "chat history: ", chatHistory

str(chatHistory)
str(routerPrompt)
str(systemPrompt)
print("main file: ")
print("Variables created")
time.sleep(3)


def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    print("main file: ")
    print("quit function executed")
    time.sleep(3)
    exit()


def router(userInput):
    
    if userInput == "/quit":
        quitCommand()
        return
    
    userInput = "User's Input: ", userInput
    str(userInput)
    response = ollama.chat(
        model = "dolphin-llama3:8b",
        messages=[
            {
                "role": "system",
                "content": str(newRouterPrompt)
            },
            {
                "role": "user",
                "content": str(userInput)
            }
        ]
    )

    routerResponse = response['message']['content']
    print("Router Response:", routerResponse)
    toolAns = toolRouter(routerResponse)
    print("Tool Manager output", toolAns)
    return toolAns



def llmComs(message):
    routerResponse = router(message)
    print("Router Function in llmComs Response: ", routerResponse)
    
    
    response = ollama.chat(
        model = "dolphin-llama3:8b",
        messages = [
            {
                "role": "system",
                "content": str(systemPrompt)
            },
            {
                "role": "user",
                "content": str(routerResponse),
            }
        ],
        stream = True
    )
    fullResponse = ""
    for chunk in response:
        if 'message' in chunk:
            content = chunk['message']['content']
            fullResponse += content
            print(content, end='', flush=True)
    saveChatHistory(message, fullResponse)











if __name__ == "__main__":    
    while True:
       userInput = input(">>")
       print("")
       llmComs(userInput)