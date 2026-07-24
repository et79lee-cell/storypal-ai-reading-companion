from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .providers import MockCompanionProvider
from .memory import InMemoryMemoryRepository
from .story_engine import StorySession, StoryStateError

ROOT = Path(__file__).resolve().parents[1]
STORIES_DIR = ROOT / "stories"
WEB_DIR = ROOT / "web-client"


def load_stories() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in STORIES_DIR.glob("*.json"):
        story = json.loads(path.read_text(encoding="utf-8"))
        result[story["id"]] = story
    return result


stories = load_stories()
sessions: dict[str, StorySession] = {}
memory_repository = InMemoryMemoryRepository()
app = FastAPI(title="StoryPal AI Reading Companion", version="1.0.0")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "mode": "mock", "stories": len(stories)}


@app.get("/api/stories")
async def story_catalog() -> list[dict[str, Any]]:
    return [
        {key: story[key] for key in ("id", "title", "summary", "age_range", "emoji", "theme")}
        for story in stories.values()
    ]


@app.get("/api/stories/{story_id}")
async def story_detail(story_id: str) -> dict[str, Any]:
    if story_id not in stories:
        raise HTTPException(404, "story not found")
    return stories[story_id]


@app.get("/api/reports/{session_id}")
async def session_report(session_id: str) -> dict[str, Any]:
    if session_id not in sessions:
        raise HTTPException(404, "session not found")
    return sessions[session_id].report()


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> dict[str, bool]:
    existed = session_id in sessions
    sessions.pop(session_id, None)
    memory_repository.delete_session(session_id)
    return {"deleted": existed}


@app.websocket("/ws")
@app.websocket("/ws/miniapp")
async def story_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    session: StorySession | None = None
    try:
        while True:
            message = await websocket.receive_json()
            command = message.get("type")
            try:
                if command == "start_story":
                    story_id = message.get("story_id", "lost-starlight")
                    if story_id not in stories:
                        raise StoryStateError("unknown story_id")
                    session_id = uuid4().hex
                    memory = memory_repository.create_session(session_id)
                    session = StorySession(
                        stories[story_id],
                        MockCompanionProvider(),
                        session_id=session_id,
                        memory=memory,
                    )
                    sessions[session.session_id] = session
                    events = session.start()
                elif session is None:
                    raise StoryStateError("start_story must be sent first")
                elif command == "sentence_complete":
                    events = session.sentence_complete()
                elif command == "interrupt_intent":
                    events = session.interrupt()
                elif command == "user_message":
                    events = await session.submit_message(str(message.get("text", "")))
                elif command == "skip_proactive_question":
                    events = session.skip_proactive_question()
                elif command == "answer_complete":
                    events = session.answer_complete()
                else:
                    raise StoryStateError(f"unsupported message type: {command}")
                for event in events:
                    await websocket.send_json(event)
            except StoryStateError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        return


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/{page_name}.html")
async def html_page(page_name: str) -> FileResponse:
    page = WEB_DIR / f"{page_name}.html"
    if not page.is_file():
        raise HTTPException(404, "page not found")
    return FileResponse(page)


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    from .config import settings

    uvicorn.run("backend.app:app", host=settings.host, port=settings.port, reload=False)
