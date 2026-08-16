from src.tools.logger import log
from src.tools.settings import ollamaRouterModel

# Variables
file = "ollamaProv.py"
model = ollamaRouterModel


def ollamaComm(sysMsg, usrMsg, isStreaming, responseFormat=None):
    import ollama

    log("DEBUG", f"{file}: ollama provider function started")

    log("DEBUG", f"{file}: Ollama chat started")
    chatArguments = {
        "model": model,
        "messages": [
            {"role": "system", "content": str(sysMsg)},
            {"role": "user", "content": str(usrMsg)},
        ],
        "stream": isStreaming,
    }
    if responseFormat is not None:
        chatArguments["format"] = responseFormat

    response = ollama.chat(**chatArguments)
    log("debug", f"{file}: ollama chat ended")

    if isStreaming == True:
        log("debug", f"{file}: Ollama streaming response path")

        fullResponse = ""
        for chunk in response:
            print(chunk["message"]["content"], end="", flush=True)
            fullResponse = fullResponse + str(chunk["message"]["content"])

        log("info", f"{file}: Returning data -- {fullResponse}")
        return fullResponse

    elif isStreaming == False:
        log("debug", f"{file}: not streaming response path")
        log("info", f"{file}: returning non-streaming response")

        return response["message"]["content"]
