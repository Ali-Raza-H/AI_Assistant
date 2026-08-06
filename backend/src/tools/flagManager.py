from src.tools.logger import log

file = "flagManager.py"

# Class for flags declaration
class flags:

    isLooping = True
    doRemember = False

    def setLoopState(state):
        log("info", f"{file}: Setting Loop state to {state}")
        flag.isLooping = state

    def setMemState(state):
        log("info" f"{file}: Setting Router History state to {state}")