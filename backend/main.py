import ollama
from src.tools.chatHistoryTools import wipeChatHistory, saveChatHistory
from modules.toolManager import toolRouter
from src.tools.logger import log
from src.tools.prompts import routerPrompt, llmPrompt

#System prompts
newRouterPrompt = routerPrompt
systemPrompt = llmPrompt

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
    response = ollama.chat(
        model = "llama3.1:8b-instruct-q4_K_M",
        messages = [
            {
                "role": "system",
                "content": str(systemPrompt)
            },
            {
                "role": "user",
                "content": str(f"Router's response: {routerResponse} Users messege: {message}"),
            }
        ],
        stream = True
    )
    log("debug", "main.py: Main llm communication ended")
    
    
    log("debug", "streaming main llm answer")
    fullResponse = ""
    for chunk in response:
        if 'message' in chunk:
            content = chunk['message']['content']
            fullResponse += content
            print(content, end='', flush=True)
    
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