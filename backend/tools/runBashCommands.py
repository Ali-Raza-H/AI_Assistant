import json
import os
import subprocess
from tools.PATHS import *
import time

def runCommands():
    
    with open(COMMANDS_PATH, "r") as f:
        jsonReturn = json.load(f)
    for runBash in jsonReturn:
        #os.system(jsonReturn[runBash])
        commandsOutput = subprocess.check_output(jsonReturn[runBash], shell=True)
        #print(commandsOutput)
        print("runBashCommands file:")
        print("Running commands function used")
        time.sleep(3)
        return commandsOutput

