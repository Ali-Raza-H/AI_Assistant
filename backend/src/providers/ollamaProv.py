import time

from src.tools.logger import log
from src.tools.settings import ollamaCielModel, ollamaRouterModel

# Variables
file = "ollamaProv.py"
model = ollamaRouterModel


def ollamaComm(sysMsg, usrMsg, isStreaming):
    import ollama

    log("DEBUG", f"{file}: ollama provider function started")

    log("DEBUG", f"{file}: Ollama chat started")
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": str(sysMsg)},
            {"role": "user", "content": str(usrMsg)},
        ],
        stream=isStreaming,
    )
    log("debug", f"{file}: ollama chat ended")

    if isStreaming == True:
        log("debug", "{file}: Ollama streaming response path")

        fullResponse = ""
        for chunk in response:
            print(chunk["message"]["content"], end="", flush=True)
            fullResponse = fullResponse + str(chunk["message"]["content"])

        log("info", f"{file}: Returning data -- {fullResponse}")
        return fullResponse

    elif isStreaming == False:
        log("debug", f"{file}: not streaming response path")
        log("info", f"{file}: returning data -- {response['message']['content']}")

        return response["message"]["content"]
