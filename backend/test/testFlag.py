import json
import subprocess


def runCommands():

    with open("testDat/testSchema.json", "r") as f:
        jsonReturn = json.load(f)

    for runBash in jsonReturn:
        try:
            commandsOutput = subprocess.check_output(jsonReturn[runBash], shell=True)
            return commandsOutput
        except Exception as e:
            print("Error encounterd: {e}")


def toolRouter(routerInput):
    inputJson = json.loads(routerInput)

    if inputJson["tool"] == "runBash":
        with open(testDat/testSchema.json, "w") as f:
            json.dump({"action": inputJson["action"]}, f)
        return runCommands()

    elif inputJson["tool"] == "llmCom":
        log("debug", "toolManager.py: Using llmComs tool")

        userMsg = inputJson["action"]
        log("info", f"toolManager.py: llmComs returning {userMsg}")

        return userMsg


