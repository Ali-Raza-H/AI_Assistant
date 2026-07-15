import json
import os
from tools.runBashCommands import *
from tools.PATHS import *
from tools.jsonTools import fixJson
import time

def toolRouter(routerInput):
    
    try:
        inputJson = json.loads(routerInput)
        usrMsg = None
        
        if inputJson["tool"] == "runBash":
            print("Using tools")
            time.sleep(3)
            with open(COMMANDS_PATH, "w") as f:
                json.dump({"action": inputJson["action"]}, f)
            print("toolManager file:")
            print("Commands running route used")
            return runCommands()    
            time.sleep(3)    
        
        elif inputJson["tool"] == "llmCom":
            print("Using llmComs")
            time.sleep(3)
            userMsg = inputJson["action"]
            print("toolManager file:")
            print("LLM Comms route used")
            time.sleep(3)
            return userMsg
    except json.JSONDecodeError:
        print("Error: json.JSONDecodeError")
        nwJson = fixJson(routerInput)
        print(newJson)
        print("toolManager file:")
        print("fix json route used")
        time.sleep(3)
        toolRouter(nwJson)
        
        