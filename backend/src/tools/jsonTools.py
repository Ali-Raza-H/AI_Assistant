import ast
import json

from src.tools.logger import log


def fixJson(inpJson):
    log("debug", "jsonTools.py: fixJson function started")

    rawContent = inpJson.strip()
    if rawContent.startswith("```"):
        lines = rawContent.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        rawContent = "\n".join(lines).strip()

    try:
        fxJson = json.loads(rawContent)
    except json.JSONDecodeError:
        fxJson = ast.literal_eval(rawContent)
    validJson = json.dumps(fxJson)

    log("debug", "jsonTools.py: fixJson function finished")
    log("info", f"jsonTools.py: fixed JSON output {validJson}")
    return validJson
