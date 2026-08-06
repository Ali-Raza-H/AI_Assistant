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


#Function to handle quit command

def quitCommand():
    wipeChatHistory()
    print("Goodbye")
    log("debug", "Main.py: quit function executed")
    exit()




#####################################
#       MAIN ROUTER FUNCTION        #
#####################################


def router(userMsg):

    # Handle quit command
    if userMsg == "/quit":
        quitCommand()
        return


    #Setting valuse that will go into the llm Communication
    userInp = f"User's Input: {userMsg}"
    if doRemember == True:
        routerHistory = loadRouterHistory
        sysPrompt += routerHistory
    else:
        sysPrompt = routerPrompt

    routerOut = ollamaComm(sysPrompt, userInp, False)

    toolAns = toolRouter(routerOut)
    return toolAns