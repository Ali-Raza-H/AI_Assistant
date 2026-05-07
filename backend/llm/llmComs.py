import ollama
import os
import json
import datetime
from tools.chatHistoryTools import *
from tools.runBashCommands import *


#fuction to exit the cli assistant
def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    exit()


def streamAnswer(message):

    #Variables
    tools = []
    dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # gets current date time for llm
    #load chat memory fron json
    chatMemory = json.load(open(historyJsonPath))
    systemPrompt = {
        "Prompt" : "You are a helpfull assistant that answer questions and calls tools available as needed",
        "Chat Memory: " : chatMemory,
        "Current Date Time" : str(dateTimeNow),
    }

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
                "content": message,
            }
        ], stream = True
    )

    #stream answer back to user
    fullMessage=""
    for part in response:
        fullMessage = fullMessage + part['message']['content']
        print(part['message']['content'], end='', flush=True)
    
    #Save chat history to json file
    saveChatHistory(message, fullMessage)
    print("\n")