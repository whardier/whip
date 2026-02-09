"""Smart event queue for bridging async WebSocket to sync pynput.

This module provides an event queue with intelligent handling of different
event types to optimize performance and maintain correctness:
- Mouse movement: Deduplicates to keep only latest position (prevents lag)
- Keyboard events: Strict FIFO ordering with no drops (guarantees correctness)
"""

import asyncio
from collections import deque
from whip.protocol import MessageType


class EventQueue:
    """
    Smart event queue for bridging async WebSocket to sync pynput.

    Mouse move dedup: When new mouse_move arrives, replace ALL pending
    mouse_move events with the latest position. Only most recent position
    matters to minimize replay lag.

    Keyboard FIFO: Strict order preservation. Every key_down and key_up
    processed in exact order received - no skipping ever.
    """

    def __init__(self):
        self._queue: deque = deque()
        self._latest_mouse_pos: dict | None = None  # Track latest mouse position
        self._has_pending_mouse: bool = False
        self._lock = asyncio.Lock()

    async def put(self, event: dict) -> None:
        """Add event to queue with smart deduplication."""
        async with self._lock:
            event_type = event.get("type")

            if event_type == MessageType.MOUSE_MOVE:
                # Replace pending mouse position (dedup)
                self._latest_mouse_pos = event
                self._has_pending_mouse = True
            else:
                # Keyboard and other events: strict FIFO
                # First, flush any pending mouse position
                if self._has_pending_mouse:
                    self._queue.append(self._latest_mouse_pos)
                    self._has_pending_mouse = False
                    self._latest_mouse_pos = None
                self._queue.append(event)

    async def get(self) -> dict | None:
        """Get next event from queue. Returns None if empty."""
        async with self._lock:
            # Check for pending mouse position first
            if self._has_pending_mouse:
                event = self._latest_mouse_pos
                self._has_pending_mouse = False
                self._latest_mouse_pos = None
                return event

            if self._queue:
                return self._queue.popleft()
            return None

    async def get_blocking(self, timeout: float = 0.1) -> dict | None:
        """Get next event, waiting up to timeout if queue is empty."""
        event = await self.get()
        if event is not None:
            return event

        # Poll with small sleep (avoid busy loop)
        await asyncio.sleep(timeout)
        return await self.get()

    @property
    def backlog_size(self) -> int:
        """Return number of pending events for monitoring."""
        size = len(self._queue)
        if self._has_pending_mouse:
            size += 1
        return size

    @property
    def has_pending(self) -> bool:
        """Check if queue has any pending events."""
        return bool(self._queue) or self._has_pending_mouse
