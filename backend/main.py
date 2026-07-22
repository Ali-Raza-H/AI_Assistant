import ollama
from src.tools.chatHistoryTools import wipeChatHistory, saveChatHistory, loadChatHistory
from modules.toolManager import toolRouter
from src.tools.logger import log
from src.tools.vars import routerPrompt, llmPrompt, nvAPI, cielModel, provider, gAPI
from src.llmCom import nvidiaComm, geminiComm


#System prompts
newRouterPrompt = routerPrompt
systemPrompt = llmPrompt


#NVIDIA Settings
aKey = gAPI
prov = provider
model = cielModel

log("info", "Main.py: Variables created")


def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    log("debug", "Main.py: quit function executed")
    exit()


def router(userInput):
    
    log("debug", "main.py: router function started")
    
    if userInput == "/quit":
        quitCommand()
        return
    
    userInput = f"User's Input: {userInput}"
    
    log("debug", "main.py: ollama communication started")
    response = ollama.chat(
        model = "qwen2.5:1.5b-instruct",
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
    log("debug", "main.py: ollama communication ended")


    routerResponse = response['message']['content']
    toolAns = toolRouter(routerResponse)
    
    #Logging responses
    log("info", f"main.py: Router Response: {routerResponse}")
    log("info", f"main.py: Tool Manager output: {toolAns}")
    
    return toolAns



def llmComs(message):
    log("debug", "main.py: llmComs function started")
    
    
    routerResponse = router(message)
    
    
    log("info", f"main.py: llmComs function router function output recived: {routerResponse}")
    log("debug", "main.py: Main llm communication started")
    
    
    chatHistory = loadChatHistory()
    systemPrompt = f"{llmPrompt} -Chat Hisotry: {chatHistory}"

    message = f"Router Response: {routerResponse}, User's message: {message}"
    #fullResponse = nvidiaComm(aKey, prov, model, systemPrompt, message)
    fullResponse = geminiComm(aKey, prov, model, systemPrompt, message)


    log("debug", "main.py: Main llm communication ended")
    log("debug", "streaming main llm answer")
    log("debug", "main.py: Function to save chat history called")
    
    
    saveChatHistory(message, fullResponse)




def main():
    try:
        while True:
            print("")
            userInput = input(">>   ")
            print("")
            llmComs(userInput)
    
    except Exception as e:
        log("error", f"main.py: main function error: {e}")
        print(f"Error: {e}")
        quitCommand()





if __name__ == "__main__":    
    main()