import json
from src.tools.logger import log
from modules.toolManager import toolRouter
from src.providers.ollamaProv import ollamaComm
from src.tools.settings import routerPrompt
from src.tools.settings import ROUTER_HISTORY_PATH
from src.tools.flagManager import flags

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
    log("debug", f"{file}: quit function executed")
    exit()




#####################################
#       MAIN ROUTER FUNCTION        #
#####################################


def router(userMsg):

    # Handle quit command
    if userMsg == "/quit":
        log("debug", f"{file}: Quit function used")
        quitCommand()
        return


    #Setting valuse that will go into the llm Communication
    log("debug", f"{file}: Setting up variables for router's llm")

    userInp = f"User's Input: {userMsg}"
    if flags.doRemember == True:

        log("debug", f"{file}: doRemember flag true")

        routerHistory = loadRouterHistory
        sysPrompt += routerHistory

        log("info", f"{file}: router history loaded into router prompt {sysPrompt}")

    else:
        sysPrompt = routerPrompt

    log("debug", f"{file}: Ollama communication for router started")
    routerOut = ollamaComm(sysPrompt, userInp, False)

    log("debug", f"{file}: Sending router output to tool manager")
    toolAns = toolRouter(routerOut)
    log("info", f"{file}: Tool manager output -- {toolAns}")

    return toolAns