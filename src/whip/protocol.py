"""WebSocket message protocol for WHIP.

This module defines the JSON message protocol for bidirectional communication
between the browser client and server. It supports mouse events (move, down, up)
and keyboard events (down, up), along with control messages (echo, ping, pong).
"""

from enum import StrEnum
from typing import TypedDict, Any


class MessageType(StrEnum):
    """Message type identifiers for WebSocket protocol."""

    MOUSE_MOVE = "mouse_move"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    ECHO = "echo"  # For testing
    PING = "ping"
    PONG = "pong"


class MouseMoveData(TypedDict):
    """Payload for mouse move events."""

    x: float  # Normalized X coordinate (0.0-1.0)
    y: float  # Normalized Y coordinate (0.0-1.0)
    timestamp: float  # Client-side timestamp (milliseconds since epoch)


class MouseButtonData(TypedDict):
    """Payload for mouse button events (down/up)."""

    button: str  # "left", "right", or "middle"
    x: float  # Normalized X coordinate at click location
    y: float  # Normalized Y coordinate at click location


class KeyData(TypedDict):
    """Payload for keyboard events (down/up)."""

    key: str  # Key value (e.g., "a", "Enter", "ArrowUp")
    code: str  # Physical key code (e.g., "KeyA", "Enter", "ArrowUp")


class EchoData(TypedDict):
    """Payload for echo test messages."""

    message: str  # Test message content


class Message(TypedDict):
    """Generic message structure for WebSocket protocol."""

    type: MessageType  # Message type identifier
    data: dict[str, Any]  # Payload (structure varies by type)
    timestamp: float | None  # Optional server-side timestamp


def create_message(type: MessageType, data: dict[str, Any]) -> dict[str, Any]:
    """Create a well-formed message for sending.

    Args:
        type: Message type identifier
        data: Message payload (must match expected structure for the type)

    Returns:
        JSON-serializable dict with type and data fields
    """
    return {"type": type, "data": data}


def parse_message(raw: dict[str, Any]) -> Message:
    """Parse and validate incoming message.

    Args:
        raw: Raw JSON object received from WebSocket

    Returns:
        Validated Message object

    Raises:
        KeyError: If required fields are missing
        ValueError: If message type is invalid
    """
    msg_type = raw.get("type")
    if msg_type not in MessageType.__members__.values():
        raise ValueError(f"Invalid message type: {msg_type}")

    return {
        "type": MessageType(msg_type),
        "data": raw.get("data", {}),
        "timestamp": raw.get("timestamp"),
    }
