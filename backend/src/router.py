import json
from src.tools.logger import log
from modules.toolManager import toolRouter
from src.providers.ollamaProv import ollamaComm
from src.tools.settings import routerPrompt
from src.tools.settings import ROUTER_HISTORY_PATH


# VARIABLES
file = "router.py"
sysPrompt = routerPrompt
path = ROUTER_HISTORY_PATH


# Function to load router's history

def loadRouterHistory():
    log("debug", f"{file} load router history function started")

    with open(path, "r") as routerHistoryData:
        routerHistory = json.load(routerHistoryData)

        log("debug", f"{file} load chat history function finished")
        log("info", f"{file} Router chat history returning {routerHistory}")

    return routerHistory




#####################################
#       MAIN ROUTER FUNCTION        #
#####################################


def router(userMsg):

    log("debug", f"{file}: Router function started")
    log("info", f"{file}: Router function input {userMsg}")

    userInp = f"User's Input: {userMsg}"

    log("debug", f"{file}: Ollama Communication started")
    log("info", f"{file}: Data to be sent to ollama -- user's message - {userInp}")

    routerOut = ollamaComm(sysPrompt, userInp, False)
    