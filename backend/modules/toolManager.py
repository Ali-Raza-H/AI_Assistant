import json
from modules.runBashCommands import runCommands
from src.tools.vars import COMMANDS_PATH
from src.tools.jsonTools import fixJson
from src.tools.logger import log


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
        
        
        elif inputJson["tool"] == "llmCom":
            log("debug", "toolManager.py: Using llmComs tool")
            
            userMsg = inputJson["action"]
            log("info", f"toolManager.py: llmComs returning {userMsg}")
            
            return userMsg
    
    
    except json.JSONDecodeError:
        log("error", f"toolManager.py: json.JSONDecodeError {routerInput}")
            
        log("debug", "toolManager.py: using fixJson function")
        nwJson = fixJson(routerInput)
        log("info", f"toolManager.py: fixed json {nwJson}")
    
        log("debug", "toolManager.py: Calling toolRouter again")
        
        nwCall = toolRouter(nwJson)
        return nwCall
        