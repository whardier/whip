"""Unit tests for EventQueue with mouse deduplication and keyboard FIFO."""

import pytest
from whip.queue import EventQueue
from whip.protocol import MessageType


@pytest.mark.asyncio
async def test_mouse_dedup_keeps_only_latest():
    """Multiple mouse moves should keep only the latest position."""
    q = EventQueue()

    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 0, "y": 0}})
    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 50, "y": 50}})
    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 100, "y": 100}})

    # Should only get the latest position
    event = await q.get()
    assert event["data"]["x"] == 100
    assert event["data"]["y"] == 100

    # Queue should be empty now
    assert await q.get() is None


@pytest.mark.asyncio
async def test_keyboard_fifo_order():
    """Keyboard events must preserve exact order."""
    q = EventQueue()

    await q.put({"type": MessageType.KEY_DOWN, "data": {"key": "a"}})
    await q.put({"type": MessageType.KEY_DOWN, "data": {"key": "b"}})
    await q.put({"type": MessageType.KEY_UP, "data": {"key": "a"}})
    await q.put({"type": MessageType.KEY_UP, "data": {"key": "b"}})

    # Must get exact order
    e1 = await q.get()
    e2 = await q.get()
    e3 = await q.get()
    e4 = await q.get()

    assert e1["data"]["key"] == "a" and e1["type"] == MessageType.KEY_DOWN
    assert e2["data"]["key"] == "b" and e2["type"] == MessageType.KEY_DOWN
    assert e3["data"]["key"] == "a" and e3["type"] == MessageType.KEY_UP
    assert e4["data"]["key"] == "b" and e4["type"] == MessageType.KEY_UP


@pytest.mark.asyncio
async def test_keyboard_never_dropped():
    """Keyboard events must never be dropped, even with heavy mouse traffic."""
    q = EventQueue()

    # Simulate: mouse move, key down, many mouse moves, key up
    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 0, "y": 0}})
    await q.put({"type": MessageType.KEY_DOWN, "data": {"key": "x"}})
    for i in range(100):
        await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": i, "y": i}})
    await q.put({"type": MessageType.KEY_UP, "data": {"key": "x"}})

    # Drain queue, counting keyboard events
    keyboard_events = []
    while True:
        event = await q.get()
        if event is None:
            break
        if event["type"] in (MessageType.KEY_DOWN, MessageType.KEY_UP):
            keyboard_events.append(event)

    # Both keyboard events must be present
    assert len(keyboard_events) == 2
    assert keyboard_events[0]["type"] == MessageType.KEY_DOWN
    assert keyboard_events[1]["type"] == MessageType.KEY_UP


@pytest.mark.asyncio
async def test_mixed_events_order():
    """Mouse flush happens before keyboard, preserving logical order."""
    q = EventQueue()

    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 10, "y": 10}})
    await q.put({"type": MessageType.KEY_DOWN, "data": {"key": "k"}})

    # Mouse should come first (flushed when keyboard arrived)
    e1 = await q.get()
    e2 = await q.get()

    assert e1["type"] == MessageType.MOUSE_MOVE
    assert e2["type"] == MessageType.KEY_DOWN


@pytest.mark.asyncio
async def test_backlog_size():
    """Backlog size should reflect pending events."""
    q = EventQueue()

    assert q.backlog_size == 0

    await q.put({"type": MessageType.MOUSE_MOVE, "data": {"x": 0, "y": 0}})
    assert q.backlog_size == 1  # Pending mouse

    await q.put({"type": MessageType.KEY_DOWN, "data": {"key": "a"}})
    assert q.backlog_size == 2  # Flushed mouse + keyboard

    await q.get()  # Remove one
    assert q.backlog_size == 1
