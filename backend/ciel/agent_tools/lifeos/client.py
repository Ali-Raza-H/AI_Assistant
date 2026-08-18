from __future__ import annotations

import json
import socket
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.ciel.runtime.settings import (
    lifeOSAPIKey,
    lifeOSBaseURL,
    lifeOSMaxRetries,
    lifeOSRetryBackoffSeconds,
    lifeOSTimeoutSeconds,
)


READ_OPERATIONS = {
    "get_capabilities": ("GET", "/capabilities"),
    "get_today": ("GET", "/context/today"),
    "get_weekly_review": ("GET", "/context/weekly-review"),
    "search": ("GET", "/search"),
    "list_tasks": ("GET", "/tasks"),
    "get_task": ("GET", "/tasks/{task_id}"),
    "list_projects": ("GET", "/projects"),
    "get_project": ("GET", "/projects/{project_id}"),
    "list_goals": ("GET", "/goals"),
    "list_habits": ("GET", "/habits"),
    "list_calendar": ("GET", "/calendar"),
    "list_notes": ("GET", "/notes"),
    "list_library": ("GET", "/library/items"),
    "list_contacts": ("GET", "/contacts"),
    "list_journal": ("GET", "/journal"),
    "list_health": ("GET", "/health"),
    "list_diet": ("GET", "/diet"),
    "list_gym_routines": ("GET", "/gym/routines"),
    "list_gym_logs": ("GET", "/gym/logs"),
    "list_finance": ("GET", "/finance"),
    "list_events": ("GET", "/events"),
}

WRITE_OPERATIONS = {
    "create_task": ("POST", "/tasks"),
    "update_task": ("PATCH", "/tasks/{task_id}"),
    "complete_task": ("PATCH", "/tasks/{task_id}"),
    "create_project": ("POST", "/projects"),
    "update_project": ("PATCH", "/projects/{project_id}"),
    "create_project_milestone": ("POST", "/projects/{project_id}/milestones"),
    "update_project_milestone": ("PATCH", "/projects/{project_id}/milestones/{milestone_id}"),
    "create_goal": ("POST", "/goals"),
    "update_goal": ("PATCH", "/goals/{goal_id}"),
    "create_goal_milestone": ("POST", "/goals/{goal_id}/milestones"),
    "update_goal_milestone": ("PATCH", "/goals/{goal_id}/milestones/{milestone_id}"),
    "create_habit": ("POST", "/habits"),
    "update_habit": ("PATCH", "/habits/{habit_id}"),
    "log_habit": ("POST", "/habits/{habit_id}/logs"),
    "create_calendar_event": ("POST", "/calendar/events"),
    "update_calendar_event": ("PATCH", "/calendar/events/{event_id}"),
    "create_note": ("POST", "/notes"),
    "update_note": ("PATCH", "/notes/{note_id}"),
    "create_library_item": ("POST", "/library/items"),
    "update_library_item": ("PATCH", "/library/items/{item_id}"),
    "create_contact": ("POST", "/contacts"),
    "update_contact": ("PATCH", "/contacts/{contact_id}"),
    "create_journal": ("POST", "/journal"),
    "update_journal": ("PATCH", "/journal/{entry_id}"),
    "create_health": ("POST", "/health"),
    "create_diet": ("POST", "/diet"),
    "create_gym_log": ("POST", "/gym/logs"),
    "create_finance": ("POST", "/finance"),
    "update_finance": ("PATCH", "/finance/{entry_id}"),
    "acknowledge_event": ("POST", "/events/{event_id}/acknowledge"),
}

LIFEOS_OPERATIONS = {**READ_OPERATIONS, **WRITE_OPERATIONS}
PATH_ARGUMENTS = {
    "task_id",
    "project_id",
    "goal_id",
    "habit_id",
    "event_id",
    "note_id",
    "item_id",
    "contact_id",
    "entry_id",
    "milestone_id",
}
LIFEOS_PERMISSION_STATUS_CODES = frozenset({401, 403})
LIFEOS_PERMISSION_ERROR_CODES = frozenset(
    {
        "access_denied",
        "forbidden",
        "insufficient_permissions",
        "not_allowed",
        "permission_denied",
        "unauthorized",
    }
)


def _configured() -> bool:
    return bool(str(lifeOSBaseURL or "").strip() and str(lifeOSAPIKey or "").strip())


def _format_path(path_template: str, arguments: dict) -> tuple[str, dict]:
    remaining = dict(arguments)
    path_values = {}
    for field in PATH_ARGUMENTS:
        placeholder = "{" + field + "}"
        if placeholder not in path_template:
            continue
        value = remaining.pop(field, None)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{field} must be a positive integer")
        path_values[field] = value
    return path_template.format(**path_values), remaining


def _decode_response(raw: bytes) -> object:
    if not raw:
        return {}
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"message": text}


def _permission_error_code(data: object) -> str:
    if not isinstance(data, dict):
        return ""
    for field in ("code", "errorCode", "error_code", "type"):
        value = data.get(field)
        if isinstance(value, str):
            return value.strip().lower().replace("-", "_").replace(" ", "_")
    error = data.get("error")
    if isinstance(error, dict):
        return _permission_error_code(error)
    return ""


def isLifeOSPermissionError(result: dict) -> bool:
    if not isinstance(result, dict) or result.get("success") is True:
        return False
    if result.get("statusCode") in LIFEOS_PERMISSION_STATUS_CODES:
        return True
    if result.get("errorType") == "permission_denied":
        return True
    return _permission_error_code(result.get("data")) in LIFEOS_PERMISSION_ERROR_CODES


def runLifeOSAction(operation: str, arguments: dict | None = None) -> dict:
    if not _configured():
        return {
            "success": False,
            "statusCode": 0,
            "error": "LifeOS is not configured. Set LIFEOS_BASE_URL and LIFEOS_API_KEY.",
        }
    if operation not in LIFEOS_OPERATIONS:
        return {
            "success": False,
            "statusCode": 0,
            "error": f"Unknown LifeOS operation: {operation}",
            "availableOperations": sorted(LIFEOS_OPERATIONS),
        }
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return {"success": False, "statusCode": 0, "error": "LifeOS arguments must be an object."}

    method, path_template = LIFEOS_OPERATIONS[operation]
    try:
        path, request_arguments = _format_path(path_template, arguments)
    except ValueError as error:
        return {"success": False, "statusCode": 0, "error": str(error)}

    if operation == "complete_task":
        request_arguments["status"] = "completed"

    idempotency_key = str(request_arguments.pop("idempotency_key", "") or uuid.uuid4().hex)
    url = f"{str(lifeOSBaseURL).rstrip('/')}/api/v1/assistant{path}"
    body = None
    if method == "GET" and request_arguments:
        url = f"{url}?{urlencode(request_arguments, doseq=True)}"
    elif method != "GET":
        body = json.dumps(request_arguments).encode("utf-8")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {lifeOSAPIKey}",
        "User-Agent": "CIEL-LifeOS/1.0",
        "X-Request-ID": uuid.uuid4().hex,
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
        headers["Idempotency-Key"] = idempotency_key

    attempts = max(0, int(lifeOSMaxRetries)) + 1
    for attempt in range(attempts):
        request_object = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request_object, timeout=float(lifeOSTimeoutSeconds)) as response:
                data = _decode_response(response.read())
                return {"success": True, "statusCode": response.status, "data": data}
        except HTTPError as error:
            data = _decode_response(error.read())
            if error.code in {502, 503, 504} and attempt + 1 < attempts:
                time.sleep(float(lifeOSRetryBackoffSeconds) * (2**attempt))
                continue
            if isinstance(data, dict):
                message = data.get("message") or data.get("error")
            else:
                message = str(data)
            result = {
                "success": False,
                "statusCode": error.code,
                "error": message,
                "data": data,
            }
            if (
                error.code in LIFEOS_PERMISSION_STATUS_CODES
                or _permission_error_code(data) in LIFEOS_PERMISSION_ERROR_CODES
            ):
                result.update({"errorType": "permission_denied", "retryable": False})
            return result
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            if attempt + 1 < attempts:
                time.sleep(float(lifeOSRetryBackoffSeconds) * (2**attempt))
                continue
            return {"success": False, "statusCode": 0, "error": f"LifeOS request failed: {error}"}

    return {"success": False, "statusCode": 0, "error": "LifeOS request failed."}
