from __future__ import annotations

import asyncio
import os
import queue
import threading
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.ciel.agent_tools.lifeos.client import runLifeOSAction
from backend.ciel.core.controller import isControllerBusy, runController
from backend.ciel.core.events import eventBus
from backend.ciel.runtime.chat_history import loadChatHistory
from backend.ciel.runtime.logging import log
from backend.ciel.services.lifeos_notifications import startLifeOSNotificationListener


ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = ROOT / "frontend" / "dist"
WEB_HOST = os.getenv("CIEL_WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("CIEL_WEB_PORT", "8765"))
_webRequestLock = threading.Lock()


class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


def _chatMessages() -> list[dict]:
    messages = []
    for recordIndex, record in enumerate(loadChatHistory()):
        if not isinstance(record, dict):
            continue
        userMessage = record.get("userMessage")
        assistantResponse = record.get("assistantResponse")
        if isinstance(userMessage, str) and userMessage.strip():
            messages.append(
                {
                    "id": f"history-{recordIndex}-user",
                    "role": "user",
                    "content": userMessage,
                    "record": recordIndex,
                }
            )
        if isinstance(assistantResponse, str) and assistantResponse.strip():
            messages.append(
                {
                    "id": f"history-{recordIndex}-assistant",
                    "role": "assistant",
                    "content": assistantResponse,
                    "record": recordIndex,
                }
            )
    return messages


async def _lifeOSRead(operation: str, arguments: dict | None = None):
    return await asyncio.to_thread(runLifeOSAction, operation, arguments or {})


def createApp() -> FastAPI:
    app = FastAPI(title="CIEL Interface", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.on_event("startup")
    async def startup():
        startLifeOSNotificationListener()

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "controllerBusy": isControllerBusy()}

    @app.get("/api/state")
    async def state():
        return {"state": eventBus.snapshot(), "events": eventBus.recent()}

    @app.get("/api/chat")
    async def chat():
        return {"messages": _chatMessages()}

    @app.get("/api/dashboard")
    async def dashboard():
        operations = {
            "tasks": ("list_tasks", {"status": "pending"}),
            "calendar": ("list_calendar", {}),
            "notifications": ("list_events", {"include_acknowledged": 0}),
        }
        results = await asyncio.gather(
            *(_lifeOSRead(operation, arguments) for operation, arguments in operations.values()),
            return_exceptions=True,
        )
        dashboardData = {}
        for section, result in zip(operations, results):
            if isinstance(result, Exception) or not result.get("success"):
                continue
            dashboardData[section] = result.get("data")
        return {"sections": dashboardData}

    @app.post("/api/messages", status_code=202)
    async def message(request: MessageRequest, backgroundTasks: BackgroundTasks):
        cleanMessage = request.message.strip()
        if not cleanMessage:
            raise HTTPException(status_code=422, detail="Message cannot be empty")
        if isControllerBusy() or not _webRequestLock.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="CIEL is already handling a message")

        interactionId = eventBus.emit(
            "interaction.queued", {"message": cleanMessage}
        )["id"]

        def execute():
            try:
                runController(cleanMessage, interactionId=interactionId)
            except Exception as error:
                log("error", f"server.py: interaction failed: {error}")
            finally:
                _webRequestLock.release()

        backgroundTasks.add_task(execute)
        return {"accepted": True, "interactionId": interactionId}

    @app.websocket("/ws/events")
    async def events(websocket: WebSocket):
        await websocket.accept()
        subscription = eventBus.subscribe()
        try:
            await websocket.send_json(
                {
                    "type": "system.snapshot",
                    "timestamp": eventBus.snapshot()["updatedAt"],
                    "data": {
                        "state": eventBus.snapshot(),
                        "events": eventBus.recent(),
                    },
                }
            )
            while True:
                try:
                    event = await asyncio.to_thread(subscription.eventQueue.get, True, 15)
                    await websocket.send_json(event)
                except queue.Empty:
                    await websocket.send_json(
                        {"type": "system.ping", "timestamp": eventBus.snapshot()["updatedAt"], "data": {}}
                    )
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            subscription.close()

    if FRONTEND_DIST.exists():
        assets = FRONTEND_DIST / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/{path:path}")
        async def frontend(path: str):
            requested = FRONTEND_DIST / path
            if path and requested.is_file() and FRONTEND_DIST in requested.resolve().parents:
                return FileResponse(requested)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


app = createApp()


def runServer():
    import uvicorn

    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT, log_level="warning")


def startWebServer():
    thread = threading.Thread(target=runServer, name="ciel-web", daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    runServer()
