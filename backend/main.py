import ollama
from modules.toolManager import toolRouter
from src.providers.googleProv import geminiComm
from src.providers.ollamaProv import ollamaComm
from src.providers.nvidiaProv import nvidiaComm
from src.tools.chatHistoryTools import loadChatHistory, saveChatHistory, wipeChatHistory
from src.tools.logger import log
from src.tools.settings import llmPrompt
from src.router import router
# System prompts
systemPrompt = llmPrompt


log("info", "Main.py: Variables created")

def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    log("debug", "Main.py: quit function executed")
    exit()


def llmComs(message):
    log("debug", "main.py: llmComs function started")

    routerResponse = router(message)

    log(
        "info",
        f"main.py: llmComs function router function output recived: {routerResponse}",
    )
    log("debug", "main.py: Main llm communication started")

    chatHistory = loadChatHistory()
    systemPrompt = f"{llmPrompt} -Chat Hisotry: {chatHistory}"

    message = f"Router Response: {routerResponse}, User's message: {message}"

    #fullResponse = nvidiaComm(systemPrompt, message, True)
    fullResponse = geminiComm(systemPrompt, message, True)
    # fullResponse = ollamaComm(str(systemPrompt), str(message), True)

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
