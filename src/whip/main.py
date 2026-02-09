import signal
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from whip.protocol import MessageType
from whip.queue import EventQueue
from whip.permissions import check_accessibility_permission, print_permission_instructions
from whip.controller import InputController

app = FastAPI(title="WHIP - Web Host Input Protocol")


# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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
input_controller: InputController | None = None


async def event_consumer():
    """Background task that drains event queue and controls macOS input."""
    global input_controller
    if input_controller is None:
        return

    while True:
        event = await event_queue.get_blocking(timeout=0.05)
        if event is None:
            continue

        try:
            msg_type = event.get("type")
            data = event.get("data", {})

            if msg_type == MessageType.MOUSE_MOVE:
                input_controller.move_mouse(data.get("x", 0), data.get("y", 0))
            elif msg_type == MessageType.MOUSE_DOWN:
                input_controller.mouse_down(data.get("button", "left"), data.get("x", 0), data.get("y", 0))
            elif msg_type == MessageType.MOUSE_UP:
                input_controller.mouse_up(data.get("button", "left"), data.get("x", 0), data.get("y", 0))
            elif msg_type == MessageType.KEY_DOWN:
                input_controller.key_down(data.get("key", ""), data.get("code", ""))
            elif msg_type == MessageType.KEY_UP:
                input_controller.key_up(data.get("key", ""), data.get("code", ""))
        except Exception as e:
            print(f"[ERROR] Event processing failed: {e}")


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
                # Log incoming event for debugging
                event_data = data.get("data", {})
                if msg_type == MessageType.MOUSE_MOVE:
                    print(f"[MOUSE] move x={event_data.get('x', 0):.5f} y={event_data.get('y', 0):.5f}")
                elif msg_type == MessageType.MOUSE_DOWN:
                    print(f"[MOUSE] down button={event_data.get('button')} x={event_data.get('x', 0):.5f} y={event_data.get('y', 0):.5f}")
                elif msg_type == MessageType.MOUSE_UP:
                    print(f"[MOUSE] up button={event_data.get('button')} x={event_data.get('x', 0):.5f} y={event_data.get('y', 0):.5f}")
                elif msg_type == MessageType.KEY_DOWN:
                    print(f"[KEY] down key={event_data.get('key')} code={event_data.get('code')}")
                elif msg_type == MessageType.KEY_UP:
                    print(f"[KEY] up key={event_data.get('key')} code={event_data.get('code')}")
                else:
                    print(f"[EVENT] {msg_type}: {event_data}")

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
    global input_controller

    print("WHIP server starting...")
    print("Checking Accessibility permissions...")

    if not check_accessibility_permission():
        print("\n" + "="*60)
        print("ERROR: Accessibility permission NOT granted")
        print("="*60)
        print_permission_instructions()
        print("="*60)
        print("\nServer will start but macOS control will NOT work.")
        print("Grant permission and restart the server.")
        print("="*60 + "\n")
    else:
        print("Accessibility permission: OK")
        input_controller = InputController()
        print(f"Screen size: {input_controller._screen_width}x{input_controller._screen_height}")

        # Start background consumer task
        import asyncio
        asyncio.create_task(event_consumer())
        print("Event consumer started")

    print(f"\nWHIP server running at http://0.0.0.0:9447")
