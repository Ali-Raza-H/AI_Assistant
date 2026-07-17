import json
import subprocess
from src.tools.logger import log
from src.tools.PATHS import COMMANDS_PATH

def runCommands():
    log("debug", "runBashCommands.py: runCommands function started")
    
    log("debug", "runBashCommands.py: loading json file")
    with open(COMMANDS_PATH, "r") as f:
        jsonReturn = json.load(f)

        log("info", f"runBashCommands.py: JSON Loaded {jsonReturn}")
    
    for runBash in jsonReturn:
        try:
            commandsOutput = subprocess.check_output(jsonReturn[runBash], shell=True)

            log("debug", "runBashCommands.py: commands executed")
            log("info", f"runBashCommands.py: executed commands output {commandsOutput}")

            return commandsOutput
        
        
        except Exception as e:
            log("error", f"runbashCommands.py: Error encountered when running commands {e}")
            print("Error encounterd, Check logs")
