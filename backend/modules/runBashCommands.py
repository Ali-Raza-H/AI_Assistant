"""Shell tool implementation used by the orchestrator."""

from __future__ import annotations

import subprocess
import json
from typing import Any

from src.tools.logger import log
from src.tools.settings import COMMANDS_PATH


def runCommands(command: str | None = None) -> dict[str, Any]:
    """Run one shell command and return a serializable result."""

    if command is None:
        try:
            with open(COMMANDS_PATH, "r", encoding="utf-8") as data_file:
                saved_output = json.load(data_file)
            if isinstance(saved_output, dict):
                command = saved_output.get("action")
        except (FileNotFoundError, json.JSONDecodeError):
            command = None

    if not command:
        return {
            "success": False,
            "output": "No command was provided.",
            "returnCode": 2,
        }

    log("debug", f"runBashCommands.py: executing command {command}")
    if not isinstance(command, str):
        return {
            "success": False,
            "output": "The command must be a string.",
            "returnCode": 2,
        }

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        log("error", f"runBashCommands.py: command failed to start: {exc}")
        return {"success": False, "output": str(exc), "returnCode": 1}

    output = completed.stdout or completed.stderr
    result = {
        "success": completed.returncode == 0,
        "output": output.rstrip(),
        "returnCode": completed.returncode,
    }
    log("info", f"runBashCommands.py: command result {result}")
    return result
