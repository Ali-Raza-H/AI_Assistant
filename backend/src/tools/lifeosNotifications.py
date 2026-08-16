from __future__ import annotations

import threading
import time

from src.tools.lifeosClient import runLifeOSAction
from src.events import eventBus
from src.tools.logger import log
from src.tools.settings import (
    lifeOSAPIKey,
    lifeOSNotificationPollSeconds,
    lifeOSNotificationsEnabled,
)


file = "lifeosNotifications.py"
_listener_thread = None
_listener_lock = threading.Lock()


def _display_event(event: dict) -> None:
    severity = str(event.get("severity") or "low").upper()
    title = str(event.get("title") or event.get("event_type") or "LifeOS notification")
    message = str(event.get("message") or "").strip()
    suffix = f" — {message}" if message else ""
    print(f"\n[LifeOS {severity}] {title}{suffix}")
    eventBus.emit("lifeos.notification", {"notification": event})


def _acknowledge(event_id: int) -> bool:
    result = runLifeOSAction(
        "acknowledge_event",
        {
            "event_id": event_id,
            "idempotency_key": f"ciel-notification-{event_id}",
        },
    )
    if not result.get("success"):
        log("error", f"{file}: could not acknowledge event {event_id}")
        return False
    return True


def _poll_once(last_event_id: int) -> int:
    result = runLifeOSAction(
        "list_events",
        {"after": max(0, last_event_id), "limit": 100},
    )
    if not result.get("success"):
        log("error", f"{file}: LifeOS notification poll failed: {result.get('error', 'unknown error')}")
        return last_event_id

    data = result.get("data")
    events = data.get("events") if isinstance(data, dict) else None
    if not isinstance(events, list):
        log("error", f"{file}: LifeOS notification poll returned an invalid response")
        return last_event_id

    for event in events:
        if not isinstance(event, dict):
            continue
        event_id = event.get("id")
        if isinstance(event_id, bool) or not isinstance(event_id, int) or event_id <= last_event_id:
            continue
        _display_event(event)
        if not _acknowledge(event_id):
            break
        last_event_id = event_id
    return last_event_id


def _listen_forever() -> None:
    last_event_id = 0
    poll_seconds = max(1.0, float(lifeOSNotificationPollSeconds))

    while True:
        try:
            last_event_id = _poll_once(last_event_id)
        except Exception as error:
            log("error", f"{file}: LifeOS notification poll failed: {error}")
        time.sleep(poll_seconds)


def startLifeOSNotificationListener():
    global _listener_thread
    if not lifeOSNotificationsEnabled:
        log("info", f"{file}: LifeOS notification listener is disabled")
        return None
    if not str(lifeOSAPIKey or "").strip():
        log("info", f"{file}: LifeOS notification listener not started; API key is not configured")
        return None

    with _listener_lock:
        if _listener_thread and _listener_thread.is_alive():
            return _listener_thread
        _listener_thread = threading.Thread(
            target=_listen_forever,
            name="lifeos-notifications",
            daemon=True,
        )
        _listener_thread.start()
        log("info", f"{file}: LifeOS notification polling started")
        return _listener_thread
