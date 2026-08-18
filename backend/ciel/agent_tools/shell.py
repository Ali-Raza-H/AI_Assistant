import os
import subprocess
from typing import Any

from backend.ciel.runtime.logging import log


DEFAULT_TIMEOUT_SECONDS = max(
    1.0,
    float(os.getenv("CIEL_SHELL_TIMEOUT_SECONDS", "60")),
)


def runCommands(command: str) -> dict[str, Any]:
    log("debug", "shell.py: runCommands started")

    if not isinstance(command, str) or not command.strip():
        return {
            "success": False,
            "output": "The command must be a non-empty string.",
            "returnCode": 2,
        }

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        output_parts = []
        for part in (error.stdout, error.stderr):
            if isinstance(part, bytes):
                part = part.decode("utf-8", errors="replace")
            if part:
                output_parts.append(str(part).rstrip())
        output = "\n".join(output_parts)
        message = f"Command timed out after {DEFAULT_TIMEOUT_SECONDS:g} seconds."
        if output:
            message = f"{message}\n{output}"
        log("error", "shell.py: command timed out")
        return {
            "success": False,
            "output": message,
            "returnCode": 124,
            "timedOut": True,
        }
    except OSError as error:
        log("error", f"shell.py: command failed to start: {error}")
        return {"success": False, "output": str(error), "returnCode": 1}

    output_parts = []
    for part in (completed.stdout, completed.stderr):
        if part:
            output_parts.append(part.rstrip())
    output = "\n".join(output_parts)

    result = {
        "success": completed.returncode == 0,
        "output": output,
        "returnCode": completed.returncode,
    }

    # Do not write arbitrary shell output to logs. It may contain secrets or
    # private data. Operational metadata is sufficient for diagnostics.
    log(
        "info",
        f"shell.py: command finished returnCode={completed.returncode} success={result['success']}",
    )
    return result
