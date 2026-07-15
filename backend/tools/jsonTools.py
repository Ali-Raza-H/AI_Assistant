import json
import ast


def fixJson(inpJson):
    rawContent = inpJson
    fxJson = ast.literal_eval(rawContent)
    validJson = json.dumps(fxJson)
    print("jsonTools file:")
    print("fix json tool executed")
    time.sleep(3)
    return validJson
