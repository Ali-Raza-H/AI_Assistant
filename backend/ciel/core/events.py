from __future__ import annotations

import copy
import queue
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Callable


@dataclass
class EventSubscription:
    eventQueue: queue.Queue
    close: Callable[[], None]


class CIELEventBus:
    def __init__(self, historySize: int = 250):
        self._history = deque(maxlen=historySize)
        self._subscribers = set()
        self._lock = threading.Lock()
        self._state = {
            "status": "idle",
            "stage": "idle",
            "interactionId": None,
            "iteration": 0,
            "flags": {"isLooping": False, "doRemember": False},
            "brainDecision": None,
            "routerDecision": None,
            "tools": [],
            "observations": [],
            "lastResponse": None,
            "error": None,
            "updatedAt": time.time(),
        }

    def emit(self, eventType: str, data: dict | None = None) -> dict:
        payload = {
            "id": uuid.uuid4().hex,
            "type": eventType,
            "timestamp": time.time(),
            "data": data or {},
        }
        with self._lock:
            self._reduceState(payload)
            self._history.append(payload)
            subscribers = tuple(self._subscribers)

        for subscriber in subscribers:
            try:
                subscriber.put_nowait(payload)
            except queue.Full:
                # A slow browser must not block CIEL or the TUI.
                try:
                    subscriber.get_nowait()
                    subscriber.put_nowait(payload)
                except (queue.Empty, queue.Full):
                    pass
        return payload

    def snapshot(self) -> dict:
        with self._lock:
            return copy.deepcopy(self._state)

    def recent(self) -> list[dict]:
        with self._lock:
            return copy.deepcopy(list(self._history))

    def subscribe(self) -> EventSubscription:
        eventQueue = queue.Queue(maxsize=300)
        with self._lock:
            self._subscribers.add(eventQueue)

        def close():
            with self._lock:
                self._subscribers.discard(eventQueue)

        return EventSubscription(eventQueue=eventQueue, close=close)

    def _reduceState(self, event: dict) -> None:
        eventType = event["type"]
        data = event["data"]
        self._state["updatedAt"] = event["timestamp"]

        stageMap = {
            "context.started": "context",
            "context.completed": "context",
            "memory.retrieval.started": "memory",
            "memory.retrieval.completed": "memory",
            "brain.started": "brain",
            "brain.decision": "brain",
            "router.started": "router",
            "router.decision": "router",
            "router.completed": "router",
            "tools.started": "tools",
            "tool.started": "tools",
            "tool.completed": "tools",
            "observation.created": "observation",
            "response.started": "response",
            "response.token": "response",
            "response.completed": "response",
            "memory.evaluation.started": "memory",
            "memory.committed": "memory",
            "ciel.started": "ciel",
            "ciel.token": "ciel",
            "ciel.completed": "ciel",
            "speech.started": "speech",
            "speech.ended": "controller",
            "history.saved": "controller",
        }
        if eventType == "interaction.started":
            self._state.update(
                {
                    "status": "active",
                    "stage": "router",
                    "interactionId": data.get("interactionId"),
                    "iteration": 1,
                    "brainDecision": None,
                    "routerDecision": None,
                    "tools": [],
                    "observations": [],
                    "lastResponse": None,
                    "error": None,
                }
            )
        elif eventType in stageMap:
            self._state["status"] = "active"
            self._state["stage"] = stageMap[eventType]
            if data.get("interactionId"):
                self._state["interactionId"] = data["interactionId"]
            if data.get("iteration") is not None:
                self._state["iteration"] = data["iteration"]
        elif eventType == "interaction.completed":
            self._state["status"] = "idle"
            self._state["stage"] = "idle"
            self._state["lastResponse"] = data.get("response")
        elif eventType == "interaction.failed":
            self._state["status"] = "error"
            self._state["stage"] = "error"
            self._state["error"] = data.get("error")

        if eventType == "brain.decision":
            self._state["brainDecision"] = copy.deepcopy(data.get("decision"))
        elif eventType == "router.decision":
            self._state["routerDecision"] = copy.deepcopy(data.get("decision"))
            decision = data.get("decision") or {}
            if isinstance(decision.get("flags"), dict):
                self._state["flags"] = copy.deepcopy(decision["flags"])
        elif eventType == "tools.started":
            self._state["tools"] = copy.deepcopy(data.get("tools") or [])
        elif eventType == "tool.completed":
            toolIndex = data.get("index")
            if isinstance(toolIndex, int) and toolIndex < len(self._state["tools"]):
                self._state["tools"][toolIndex] = copy.deepcopy(data.get("result"))
        elif eventType == "flags.updated":
            self._state["flags"] = copy.deepcopy(data.get("flags") or {})
        elif eventType == "observation.created":
            self._state["observations"].append(copy.deepcopy(data.get("observation")))
            self._state["observations"] = self._state["observations"][-8:]
        elif eventType == "response.completed":
            self._state["lastResponse"] = data.get("response")


eventBus = CIELEventBus()
