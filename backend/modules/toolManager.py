import json

from modules.runBashCommands import runCommands
from src.tools.jsonTools import fixJson
from src.tools.logger import log
from src.tools.settings import COMMANDS_PATH


def toolRouter(routerInput):
    log("debug", "toolManager.py: tool router function started")
    log("info", f"toolManager.py: router input: {routerInput}")

    try:
        inputJson = json.loads(routerInput)
        usrMsg = None

        if inputJson["tool"] == "runBash":
            log("debug", "toolManager.py: Using runBash tool")

            with open(COMMANDS_PATH, "w") as f:
                json.dump({"action": inputJson["action"]}, f)

            return runCommands()

        elif inputJson["tool"] == "None":
            log("debug", "toolManager.py: Using no tool")

            return "no tool used"

    except json.JSONDecodeError:
        log("error", f"toolManager.py: json.JSONDecodeError {routerInput}")

        log("debug", "toolManager.py: using fixJson function")
        nwJson = fixJson(routerInput)
        log("info", f"toolManager.py: fixed json {nwJson}")

        log("debug", "toolManager.py: Calling toolRouter again")

        nwCall = toolRouter(nwJson)
        return nwCall