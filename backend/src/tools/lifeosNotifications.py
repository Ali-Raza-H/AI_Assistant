from __future__ import annotations

import json
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.tools.lifeosClient import runLifeOSAction
from src.events import eventBus
from src.tools.logger import log
from src.tools.settings import (
    lifeOSAPIKey,
    lifeOSBaseURL,
    lifeOSNotificationReconnectSeconds,
    lifeOSNotificationsEnabled,
    lifeOSTimeoutSeconds,
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


def _listen_forever() -> None:
    last_event_id = 0
    reconnect_seconds = max(1.0, float(lifeOSNotificationReconnectSeconds))
    stream_timeout = max(60.0, float(lifeOSTimeoutSeconds))

    while True:
        url = f"{str(lifeOSBaseURL).rstrip('/')}/api/v1/assistant/events/stream"
        headers = {
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {lifeOSAPIKey}",
            "User-Agent": "CIEL-LifeOS/1.0",
            "X-Request-ID": uuid.uuid4().hex,
        }
        if last_event_id:
            headers["Last-Event-ID"] = str(last_event_id)

        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=stream_timeout) as response:
                event_id = None
                data_lines = []
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                    if not line:
                        if data_lines:
                            event = json.loads("\n".join(data_lines))
                            if isinstance(event, dict):
                                parsed_id = event.get("id", event_id)
                                if isinstance(parsed_id, int) and parsed_id > 0:
                                    _display_event(event)
                                    if _acknowledge(parsed_id):
                                        last_event_id = max(last_event_id, parsed_id)
                                    else:
                                        raise OSError("event acknowledgement failed")
                        event_id = None
                        data_lines = []
                        continue
                    if line.startswith(":"):
                        continue
                    field, _, value = line.partition(":")
                    value = value.lstrip()
                    if field == "id" and value.isdigit():
                        event_id = int(value)
                    elif field == "data":
                        data_lines.append(value)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            log("error", f"{file}: LifeOS notification stream disconnected: {error}")

        time.sleep(reconnect_seconds)


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
        log("info", f"{file}: LifeOS notification listener started")
        return _listener_thread
