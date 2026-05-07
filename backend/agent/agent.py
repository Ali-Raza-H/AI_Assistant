import ollama
import json
import os
import subprocess
import datetime
from tools.chatHistoryTools import *

def runCommands():
    
    with open(os.path.join(os.getcwd(), "C:/Users/khada/OneDrive - The Sixth Form Bolton/Subjects/Personal Project/AI_Assistant/backend/data/temp/commands.json"), "r") as f:
        jsonReturn = json.load(f)
    for runBash in jsonReturn:
        #os.system(jsonReturn[runBash])
        commandsOutput = subprocess.check_output(jsonReturn[runBash], shell=True)
        print(commandsOutput)

def agent(message):
    systemPrompt = """
        You are an AI assistant.
        You have access to tools.
        To use a tool, respond json ONLY in this format:
        {
        "tool": "tool_name",
        "command": "command to run with the tool"
        }
        Example:
        {
        "tool": "runBash",
        "command": "dir"
        }
        Do not explain.
        Do not add extra text.
    """

    response = ollama.chat(
        model = "dolphin-llama3:8b",
        messages = [
            {
                "role": "system",
                "content": systemPrompt
            },
            {
                "role": "user",
                "content": message,
            }
        ]
    )
    responseContent = response['message']['content']
    print("LLM Response:")
    print(responseContent)
    try:
        responseJson = json.loads(responseContent)
        if responseJson['tool'] == "runBash":
            with open(os.path.join(os.getcwd(), "C:/Users/khada/OneDrive - The Sixth Form Bolton/Subjects/Personal Project/AI_Assistant/backend/data/temp/commands.json"), "w") as f:
                json.dump({"command": responseJson['command']}, f)
            runCommands()
    except json.JSONDecodeError:
        print("LLM response is not a valid JSON. Response was:")
        print(responseContent)



bashToolPrompt = """
    You are an AI agent.

    You MUST obey these rules:

    1. If using a tool, respond ONLY with valid JSON.
    2. Do NOT explain anything.
    3. Do NOT wrap JSON in markdown.
    4. Do NOT include extra text.
    5. Output must start with { and end with }

    Valid format:

    {
    "tool": "runBash",
    "command": "dir"
    }

    OR

    {
    "response": "Normal response here"
    }
"""

dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # gets current date time for llm
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