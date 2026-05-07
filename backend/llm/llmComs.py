import ollama
import json
from tools.chatHistoryTools import *
from tools.runBashCommands import *
from agent.agent import *


def streamAnswer(message):

    #Variables
    tools = [bashToolPrompt]
    chatMemory = json.load(open(historyJsonPath))

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
                "role": "system",
                "content": str(tools)
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

    try:
        responseJson = json.loads(fullMessage)
        if responseJson['tool'] == "runBash":
            with open(os.path.join(os.getcwd(), "C:/Users/khada/OneDrive - The Sixth Form Bolton/Subjects/Personal Project/AI_Assistant/backend/data/temp/commands.json"), "w") as f:
                json.dump({"command": responseJson['command']}, f)
            runCommands()
    except json.JSONDecodeError:
        print("LLM response is not a valid JSON. Response was:")
        print(fullMessage)

    #Save chat history to json file
    saveChatHistory(message, fullMessage)
    print("\n")