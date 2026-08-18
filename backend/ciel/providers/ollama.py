import subprocess

from backend.ciel.runtime.logging import log
from backend.ciel.runtime.settings import ollamaRouterModel

# Variables
file = "ollamaProv.py"
model = ollamaRouterModel
OOM_MARKERS = (
    "out of memory",
    "cuda out of memory",
    "insufficient memory",
    "not enough memory",
    "gpu memory",
    "vram",
)


def _ollamaErrorText(error):
    values = [str(error)]
    for attribute in ("error", "message", "body", "response"):
        value = getattr(error, attribute, None)
        if value is not None:
            values.append(str(value))
    return " ".join(values).lower()


def _isOutOfMemoryError(error):
    errorText = _ollamaErrorText(error)
    return any(marker in errorText for marker in OOM_MARKERS)


def _restartOllamaAfterOOM():
    log("error", f"{file}: Ollama reported exhausted VRAM; restarting the service")
    try:
        completed = subprocess.run(
            ["sudo", "-n", "systemctl", "restart", "ollama"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(
            f"Could not restart Ollama after its VRAM error: {error}"
        ) from error

    if completed.returncode != 0:
        details = (
            completed.stderr or completed.stdout or "unknown systemctl error"
        ).strip()
        raise RuntimeError(
            "Ollama ran out of VRAM, and its service could not be restarted "
            f"non-interactively: {details}"
        )
    log("info", f"{file}: Ollama service restarted after VRAM exhaustion")


def _chatWithOOMRecovery(ollama, chatArguments):
    try:
        return ollama.chat(**chatArguments)
    except Exception as error:
        if not _isOutOfMemoryError(error):
            raise
        _restartOllamaAfterOOM()

    try:
        return ollama.chat(**chatArguments)
    except Exception as error:
        if _isOutOfMemoryError(error):
            raise RuntimeError(
                "Ollama is still out of VRAM after its service was restarted"
            ) from error
        raise


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

    response = _chatWithOOMRecovery(ollama, chatArguments)
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
