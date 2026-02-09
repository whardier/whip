from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from whip.protocol import MessageType
from whip.queue import EventQueue

app = FastAPI(title="WHIP - Web Host Input Protocol")

# Determine static directory path (relative to project root)
# When running via uvicorn, cwd is typically the project root
STATIC_DIR = Path("static").resolve()

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ConnectionManager:
    """Manages WebSocket connections (single connection for MVP)."""

    def __init__(self):
        self.active_connection: WebSocket | None = None

    async def connect(self, websocket: WebSocket):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self.active_connection = websocket
        print("Client connected")

    def disconnect(self):
        """Unregister the active connection."""
        self.active_connection = None
        print("Client disconnected")


manager = ConnectionManager()
event_queue = EventQueue()


@app.get("/")
async def root():
    """Redirect root to static interface"""
    return RedirectResponse(url="/static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional communication with browser."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            # Echo back messages based on type
            msg_type = data.get("type")
            if msg_type == MessageType.ECHO:
                await websocket.send_json(data)
            elif msg_type == MessageType.PING:
                await websocket.send_json({"type": MessageType.PONG})
            else:
                # Queue for processing (Phase 3 will consume)
                await event_queue.put(data)
                await websocket.send_json({
                    "type": "ack",
                    "received": msg_type,
                    "queue_size": event_queue.backlog_size
                })

    except WebSocketDisconnect:
        manager.disconnect()
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect()


@app.on_event("startup")
async def startup_event():
    print("WHIP server running at http://0.0.0.0:9447")
