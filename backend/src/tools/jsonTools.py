import json
import ast
from src.tools.logger import log


def fixJson(inpJson):
    log("debug", "jsonTools.py: fixJson function started")

    rawContent = inpJson
    fxJson = ast.literal_eval(rawContent)
    validJson = json.dumps(fxJson)

    log("debug", "jsonTools.py: fixJson function finished")
    log("info", f"jsonTOols.py: fix json function output {validJson}")


    return validJson
