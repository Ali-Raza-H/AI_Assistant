import subprocess
from typing import Any
from backend.ciel.runtime.logging import log


def runCommands(command: str) -> dict[str, Any]:
    log("debug", "runBashCommands.py: runCommands function started")

    # ----------- Checking if it's an empty command input and wether command is string ----------- #
    if not isinstance(command, str) or not command.strip():
        # Returns error explaining command should not be empty
        return {
            "success": False,
            "output": "The command must be a non-empty string.",
            "returnCode": 2,
        }

    # ----------- Runninc commands -----------#
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

    # ----------- Exception for command not accepted ----------- #
    except OSError as error:
        log("error", f"runBashCommands.py: command failed to start: {error}")
        return {"success": False, "output": str(error), "returnCode": 1}


    # ----------- Cleans up output into readable format ----------- #
    outputParts = []
    for part in (completed.stdout, completed.stderr):
        if part:
            outputParts.append(part.rstrip())
    output = "\n".join(outputParts)


    result = {
        "success": completed.returncode == 0,
        "output": output,
        "returnCode": completed.returncode,
    }


    log("info", f"runBashCommands.py: command result {result}")
    return result
