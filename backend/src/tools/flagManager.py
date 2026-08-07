from src.tools.logger import log

file = "flagManager.py"

# Class for flags declaration
class flags:

    isLooping = True
    doRemember = False

    def setFlagState(flag, state):

        log("debug", f"{file}: Using setFlagState function")
        log("info", f"{flie}: Changing state of {flag} flag to {state}")


        if flag == "isLooping":
            flags.isLooping = state
            log("debug", f"{file}: isLooping flag changed")

        elif flag == "doRemember":
            flags.doRemember = state
            log("debug", f"{file}: doRemember flag changed")

        else:
            print("Flag input not valid")
