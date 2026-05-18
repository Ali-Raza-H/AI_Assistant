import json
import datetime
from tools.chatHistoryTools import *

#Variables
dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # gets current date time for llm
#loads tool data as tools for router
with open('backend/schemas/toolsSchema.json', 'r') as toolDat:
    tools = f"Tools Available: {toolDat}"


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
routerPrompt += tools

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


