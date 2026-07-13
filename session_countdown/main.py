from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "session_countdown" / "static"
DATA_DIR = Path(os.getenv("SESSION_COUNTDOWN_DATA_DIR", ROOT / "data"))
TIMETABLE_FILE = DATA_DIR / "timetable.json"


class Session(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    start: datetime
    end: datetime | None = None
    ground_by: datetime | None = None


class Timetable(BaseModel):
    event_name: str = Field(default="Race Event", max_length=160)
    circuit: str = Field(default="", max_length=160)
    message: str = Field(default="", max_length=240)
    sessions: list[Session] = Field(default_factory=list)
    updated_at: datetime | None = None


class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = asyncio.Lock()
        self.state = Timetable()

    async def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            await self.save(self.state)
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.state = Timetable.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"Cannot load timetable from {self.path}: {exc}") from exc

    async def save(self, timetable: Timetable) -> Timetable:
        async with self.lock:
            timetable.updated_at = datetime.now(timezone.utc)
            payload = timetable.model_dump(mode="json")
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(self.path)
            self.state = timetable
            return timetable


class Connections:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.clients.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for client in self.clients:
            try:
                await client.send_json(payload)
            except Exception:
                dead.append(client)
        for client in dead:
            self.disconnect(client)


store = Store(TIMETABLE_FILE)
connections = Connections()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await store.load()
    yield


app = FastAPI(title="SessionCountdown", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def controller() -> FileResponse:
    return FileResponse(STATIC_DIR / "controller.html")


@app.get("/display")
async def display() -> FileResponse:
    return FileResponse(STATIC_DIR / "display.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "SessionCountdown",
        "updated_at": store.state.updated_at,
        "clients": len(connections.clients),
    }


@app.get("/api/timetable", response_model=Timetable)
async def get_timetable() -> Timetable:
    return store.state


@app.put("/api/timetable", response_model=Timetable)
async def put_timetable(timetable: Timetable) -> Timetable:
    ids = [session.id for session in timetable.sessions]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Session IDs must be unique")
    timetable.sessions.sort(key=lambda session: session.start)
    saved = await store.save(timetable)
    await connections.broadcast({"type": "timetable", "payload": saved.model_dump(mode="json")})
    return saved


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await connections.connect(websocket)
    await websocket.send_json({"type": "timetable", "payload": store.state.model_dump(mode="json")})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.disconnect(websocket)
