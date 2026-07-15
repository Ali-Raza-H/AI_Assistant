import ollama
import json
import datetime
from tools.chatHistoryTools import historyJsonPath
from tools.runBashCommands import runCommands
from tools.toolManager import toolRouter
from tools.chatHistoryTools import *

#Variables
dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # gets current date time for llm
#loads tool data as tools for router
with open('backend/schemas/toolsSchema.json', 'r') as toolDat:
    tools = "Tools Available:", json.load(toolDat)


routerPrompt = """
    RESPOND ONLY IN JSON FORMAT
    JSON SCHEMA RESPONSE

    {
    "tool": "tool To be Used",
    "action": "action/response"
    }

    Example Response:
    {
    "tool": "runBash",
    "action": "start https://www.google.com"
    }
"""
routerPrompt += str(tools)
print(routerPrompt)

#load chat memory fron json
chatMemory = json.load(open(historyJsonPath))
systemPrompt = {
    "Prompt" : "You are a helpfull assistant that answer questions and calls tools available as needed",
    "Chat Memory: " : chatMemory,
    "Current Date Time" : str(dateTimeNow),
}

def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    exit()




def router(userInput):

    #llm comm
    response = ollama.chat(
        model = "dolphin-llama3:8b",
        messages=[
            {
                "role": "system",
                "content": str(routerPrompt) #change to router prompt
            },
            {
                "role": "user",
                "content": str(userInput)
            }
        ]
    )

    routerResponse = response['message']['content']
    print("Router Response:", routerResponse)
    toolRouter(routerResponse)


def llmComs(message):
    chatMemory = json.load(open(historyJsonPath))
    routerResponse = router(message)
    #handle exit command
    if message == "/quit":
        quitCommand()
        return

    #handle empty json errors
    if chatMemory == []:
        chatMemory = "New Chat"
    else:
        chatMemory = json.dumps(json.load(open(historyJsonPath)))
    
    #communication with llm and response
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
        ],stream = True
    )
    fullResponse = ""
    for chunk in response:
        if 'message' in chunk:
            content = chunk['message']['content']
            fullResponse += content
            print(content, end='', flush=True)



