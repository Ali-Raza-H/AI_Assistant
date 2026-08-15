import json
from modules.runBashCommands import runCommands
from src.tools.jsonTools import fixJson
from src.tools.settings import COMMANDS_PATH
from src.tools.flagManager import flags
from src.tools.logger import log

file = "toolManager.py"

def toolRouter(routerInput):

    log("debug", f"{file}: tool router function started")
    log("info", f"{file}: router input: {routerInput}")


#   ---------------- LOADING JSON ----------------
    try:
        log("debug", f"{file}: Trying to load routerInput as json")
        inputJson = json.loads(routerInput)
        log("debug", f"{file}: Json loaded successfully")

    except json.JSONDecodeError:
        log("error", f"{file}: JSONDecodeError with {routerInput}")
        log("debug", f"{file}: Trying auto fix json")

        nwJson = fixJson(routerInput)

        log("info", f"{file}: fixed json output -- {nwJson}")
        nwCall = toolRouter(nwJson)

        log("debug", f"{file}: Calling router function again with fixed json")
        return nwCall


#   ---------------- MANAGING FLAGS ----------------
    try:
        log("debug", f"{file}: Loading flag data to be processed")

        for flag in inputJson["flags"]:
            state = inputJson["flags"][flag]

            log("info", f"{file}: Setting flag {flag} to state {state}")
            flags.setFlagState(flag, state)

    except Exception as e:
        log("Error", f"{file} Error in managing flags: {e}")


#   ---------------- RUNNING COMMANDS ----------------
    try:
        log("debug", f"{file}: Running commands section")

        for tool in inputJson["tools"]:
            log("info", f"{file}: Running the following command -- {tool}")

            if tool["tool"] == "runBash":
                log("debug", f"{file}: Using runBash Tool")

                with open(COMMANDS_PATH, "a") as f:
                    json.dump({"action": tool["action"]}, f)

                commandOut = runCommands()

                return commandOut

    except Exception as e:
        print("Error occured check logs")
        log("error", f"{file}: Error occurred when running commands -- {e}")