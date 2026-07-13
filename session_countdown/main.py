from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "session_countdown" / "static"
DATA_DIR = Path(os.getenv("SESSION_COUNTDOWN_DATA_DIR", ROOT / "data"))
TIMETABLE_FILE = DATA_DIR / "timetable.json"


class Milestone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=160)
    time: datetime
    source: str = Field(default="manual", max_length=40)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=160)
    start: datetime
    end: datetime | None = None
    source: str = Field(default="manual", max_length=40)
    milestones: list[Milestone] = Field(default_factory=list)


class DisplayOptions(BaseModel):
    show_event: bool = True
    show_circuit: bool = True
    show_clock: bool = True
    show_next_action_label: bool = True
    show_action: bool = True
    show_countdown: bool = True
    show_session: bool = True
    show_message: bool = True
    show_connection: bool = True


class Timetable(BaseModel):
    event_name: str = Field(default="Race Event", max_length=160)
    circuit: str = Field(default="", max_length=160)
    category: str = Field(default="", max_length=160)
    message: str = Field(default="", max_length=240)
    display_options: DisplayOptions = Field(default_factory=DisplayOptions)
    sessions: list[Session] = Field(default_factory=list)
    updated_at: datetime | None = None


class ImportPreview(BaseModel):
    event_name: str
    circuit: str
    categories: list[str]
    selected_category: str | None = None
    sessions: list[Session] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: int = 0
    raw_text: str = ""


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
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.state = Timetable.model_validate(payload)

    async def save(self, timetable: Timetable) -> Timetable:
        async with self.lock:
            timetable.updated_at = datetime.now(timezone.utc)
            timetable.sessions.sort(key=lambda item: item.start)
            for session in timetable.sessions:
                session.milestones.sort(key=lambda item: item.time)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(timetable.model_dump(mode="json"), indent=2), encoding="utf-8"
            )
            temporary.replace(self.path)
            self.state = timetable
            return timetable


class Connections:
    def __init__(self) -> None:
        self.clients: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, display_id: str) -> None:
        await websocket.accept()
        self.clients[websocket] = display_id

    def disconnect(self, websocket: WebSocket) -> None:
        self.clients.pop(websocket, None)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for client in self.clients:
            try:
                await client.send_json(payload)
            except Exception:
                dead.append(client)
        for client in dead:
            self.disconnect(client)

    def displays(self) -> list[str]:
        return sorted(set(self.clients.values()))


store = Store(TIMETABLE_FILE)
connections = Connections()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await store.load()
    yield


app = FastAPI(title="SessionCountdown Controller", version="0.2.1", lifespan=lifespan)
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
        "role": "controller",
        "updated_at": store.state.updated_at,
        "displays": connections.displays(),
    }


@app.get("/api/timetable", response_model=Timetable)
async def get_timetable() -> Timetable:
    return store.state


@app.put("/api/timetable", response_model=Timetable)
async def put_timetable(timetable: Timetable) -> Timetable:
    ids = [session.id for session in timetable.sessions]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail="Session IDs must be unique")
    saved = await store.save(timetable)
    await connections.broadcast({"type": "timetable", "payload": saved.model_dump(mode="json")})
    return saved


@app.post("/api/import/pdf", response_model=ImportPreview)
async def import_pdf(file: UploadFile = File(...), category: str | None = None) -> ImportPreview:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF is too large")
    temporary = DATA_DIR / "import.pdf"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(content)
    try:
        reader = PdfReader(str(temporary))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    finally:
        temporary.unlink(missing_ok=True)
    return parse_schedule(text, category)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, display_id: str = "Display") -> None:
    await connections.connect(websocket, display_id)
    await websocket.send_json({"type": "timetable", "payload": store.state.model_dump(mode="json")})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.disconnect(websocket)


def parse_schedule(text: str, selected_category: str | None) -> ImportPreview:
    clean = re.sub(r"[\u00ad\u200b\ufffe]", "", text)
    categories = sorted(set(re.findall(
        r"(?:\d{1,2}\.\d{2}(?:/\d{1,2}\.\d{2})?\s+(?:\d+´\s+)?)"
        r"(E4 Championship|FIA Formula Regional|Euroformula Open|GT Cup Europe|International GT Open)",
        clean,
        flags=re.IGNORECASE,
    )), key=str.lower)
    canonical = {value.lower(): value for value in categories}
    category = canonical.get((selected_category or "").lower()) if selected_category else None

    event_name = "Race Event"
    event_match = re.search(r"(?im)^([A-Z][A-Z ]{2,})\s*\n\s*\d{1,2}\s*-\s*\d{1,2}\s+\w+\s+20\d{2}", clean)
    if event_match:
        event_name = event_match.group(1).title()
    elif "Paul Ricard" in clean:
        event_name = "Paul Ricard"
    circuit = event_name

    warnings: list[str] = []
    sessions: list[Session] = []
    if category:
        sessions = extract_sessions(clean, category, warnings)
    confidence = 35
    confidence += 15 if event_name != "Race Event" else 0
    confidence += 20 if categories else 0
    confidence += 25 if sessions else 0
    confidence += 5 if not warnings else 0
    return ImportPreview(
        event_name=event_name,
        circuit=circuit,
        categories=categories,
        selected_category=category,
        sessions=sessions,
        warnings=warnings,
        confidence=min(confidence, 100),
        raw_text=clean[:12000],
    )


def extract_sessions(text: str, category: str, warnings: list[str]) -> list[Session]:
    year_match = re.search(r"20\d{2}", text)
    year = int(year_match.group(0)) if year_match else datetime.now().year
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    current_date: tuple[int, int, int] | None = None
    result: list[Session] = []
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        day = re.search(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^,]*,\s*(\d{1,2})\s+([A-Za-z]+)", line, re.I)
        if day:
            month = month_map.get(day.group(2).lower())
            if month:
                current_date = (year, month, int(day.group(1)))
            continue
        if not current_date or category.lower() not in line.lower():
            continue
        match = re.match(r"(\d{1,2})\.(\d{2})(?:/(\d{1,2})\.(\d{2}))?\s+(.+)$", line, re.I)
        if not match:
            continue
        hour, minute = int(match.group(1)), int(match.group(2))
        end_hour = int(match.group(3)) if match.group(3) else None
        end_minute = int(match.group(4)) if match.group(4) else None
        remainder = match.group(5).strip()
        remainder = re.sub(r"^\d+´\s+", "", remainder)
        remainder = re.sub(r"^\(TV Live\)\s+", "", remainder, flags=re.I)
        event_text = re.sub(re.escape(category), "", remainder, flags=re.I).strip(" -")
        if not re.search(r"Free practice|Qualifying|Race", event_text, re.I):
            continue
        name = normalize_session_name(event_text)
        start = datetime(*current_date, hour, minute)
        end = datetime(*current_date, end_hour, end_minute) if end_hour is not None else None
        session = Session(name=name, start=start, end=end, source="pdf")
        if re.search(r"Race", name, re.I):
            session.milestones.extend(extract_nearby_milestones(lines, index, current_date, start))
        result.append(session)
    if not result:
        warnings.append(f"No sessions were recognised for {category}")
    return result


def normalize_session_name(value: str) -> str:
    value = re.sub(r"Standing start.*$|Rolling start.*$", "", value, flags=re.I).strip(" -")
    value = re.sub(r"\(.*?\)", "", value).strip()
    return re.sub(r"\s+", " ", value)


def extract_nearby_milestones(lines: list[str], race_index: int, date_parts: tuple[int, int, int], race_start: datetime) -> list[Milestone]:
    names = {
        "pre-grid": "Cars ready on Pre Grid", "cars ready": "Cars ready on Pre Grid",
        "trolleys": "Trolleys to Pit Lane", "cars to access pitlane": "Cars to Pit Lane",
        "fast lane open": "Fast Lane Open", "pit lane open": "Pit Lane Open",
        "pit lane closed": "Pit Lane Closed", "5 min": "5 Minute Board",
        "3 min": "3 Minute Board", "1 min": "1 Minute Board / Engine On",
        "green flag": "Formation Lap",
    }
    events: list[Milestone] = []
    procedure_lines: list[str] = []
    for line in reversed(lines[max(0, race_index - 30):race_index]):
        if re.match(r"\d{1,2}\.\d{2}\s+Race\s*[–-]", line, re.I):
            break
        procedure_lines.append(line)
    for line in reversed(procedure_lines):
        time_match = re.match(r"(\d{1,2})\.(\d{2})(?:\s*/\s*tbc)?\s+(.+)", line, re.I)
        if not time_match:
            continue
        candidate = datetime(*date_parts, int(time_match.group(1)), int(time_match.group(2)))
        if candidate > race_start or (race_start - candidate).total_seconds() > 3 * 3600:
            continue
        description = time_match.group(3).lower()
        label = next((label for key, label in names.items() if key in description), None)
        if label:
            events.append(Milestone(name=label, time=candidate, source="pdf"))
    events.append(Milestone(name="Session Start", time=race_start, source="pdf"))
    dedup = {(item.name, item.time): item for item in events}
    return sorted(dedup.values(), key=lambda item: item.time)
