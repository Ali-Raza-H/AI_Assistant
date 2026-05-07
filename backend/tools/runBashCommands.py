import json
import os
import subprocess

def runCommands():
    
    with open(os.path.join(os.getcwd(), "C:/Users/khada/OneDrive - The Sixth Form Bolton/Subjects/Personal Project/AI_Assistant/backend/data/temp/commands.json"), "r") as f:
        jsonReturn = json.load(f)
    for runBash in jsonReturn:
        #os.system(jsonReturn[runBash])
        commandsOutput = subprocess.check_output(jsonReturn[runBash], shell=True)
        print(commandsOutput)
