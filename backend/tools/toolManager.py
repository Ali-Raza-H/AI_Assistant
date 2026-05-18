import json
import os
from tools.runBashCommands import *

def toolRouter(routerInput):
    inputJson = json.loads(routerInput)
    
    if inputJson['tool'] == "runBash":
        with open(os.path.join(os.getcwd(), "C:/Users/khada/OneDrive - The Sixth Form Bolton/Subjects/Personal Project/AI_Assistant/backend/schemas/temp/commands.json"), "w") as f:
            json.dump({"action": inputJson['action']}, f)
        return runCommands()
    
    elif inputJson['tool'] == "llmComs":
        pass


