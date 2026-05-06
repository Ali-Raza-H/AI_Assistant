import ollama
import os
import requests
import json
import datetime

from tools.jsonTools import *

def quitCommand():
    wipeChatHistory()
    print("Goodbye!")
    exit()

#Ollama response is printed as it is being generated
def streamAnswer(message):
    if message == "/quit":
        quitCommand()
        return
    
    dateTimeNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chatMemory = json.load(open(historyJsonPath))
    if chatMemory == []:
        chatMemory = "No previous chat history."
    else:
        chatMemory = json.dumps(json.load(open(historyJsonPath)))

    systemPrompt = {
        "Prompt": "You are a helpful assistant that answers the user's question to the best of your ability. If you don't know the answer, say you don't know. Always try to be helpful and polite.",
        "This is chat memory: " : chatMemory,
        "Current date and time: " : str(dateTimeNow)
    }
    response = ollama.chat(model="dolphin-llama3:8b", messages=[
        {
            "role": "system",
            "content": str(systemPrompt)
        },

        {
            "role": "user",
            "content": message,
        }
    ], stream=True
    )
    fullMessage = ""
    for chunk in response:
        fullMessage =  fullMessage + chunk['message']['content']
        print(chunk['message']['content'], end='', flush=True)
    
    saveChatHistory(message, fullMessage)
    print("\n")
    #print(jsonData)
    #print(chatMemory)





if __name__ == "__main__":
    while True:
        userInput = input(">> ")
        streamAnswer(userInput)