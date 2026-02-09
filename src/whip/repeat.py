"""Server-side keyboard repeat using asyncio timers.

This module provides the KeyRepeatManager class, which handles key repeat
timing on the server side for consistent cross-platform behavior. When a key
is held down, the manager waits for an initial delay, then sends repeated
key_down events at a consistent rate until the key is released.
"""

import asyncio
from whip.controller import InputController


class KeyRepeatManager:
    """Manages keyboard repeat timing for held keys.

    Uses asyncio tasks to implement key repeat with an initial delay followed
    by periodic repeats at a fixed rate. Each held key gets its own task.
    """

    def __init__(self, controller: InputController) -> None:
        """Initialize repeat manager.

        Args:
            controller: InputController instance to send key events
        """
        self._controller = controller
        self._repeat_tasks: dict[str, asyncio.Task] = {}
        self._repeat_delay: float = 0.5  # Initial delay before repeat starts (500ms)
        self._repeat_rate: float = 0.033  # Time between repeats (~30Hz)

    def start_repeat(self, key: str, code: str) -> None:
        """Start repeating a key if not already repeating.

        Args:
            key: Key character value (e.g., "a", "Enter")
            code: Physical key code (e.g., "KeyA", "Enter")
        """
        # If key is already repeating, ignore
        if key in self._repeat_tasks:
            return

        # Create and store repeat task
        task = asyncio.create_task(self._repeat_key_loop(key, code))
        self._repeat_tasks[key] = task

    def stop_repeat(self, key: str) -> None:
        """Stop repeating a key.

        Args:
            key: Key character value to stop repeating
        """
        # Cancel the task if it exists
        if key in self._repeat_tasks:
            task = self._repeat_tasks[key]
            task.cancel()
            del self._repeat_tasks[key]

    async def _repeat_key_loop(self, key: str, code: str) -> None:
        """Async loop that sends repeated key_down events.

        Waits for initial delay, then sends key_down events at repeat_rate
        until the task is cancelled (when key is released).

        Args:
            key: Key character value
            code: Physical key code
        """
        try:
            # Wait for initial delay before starting repeat
            await asyncio.sleep(self._repeat_delay)

            # Loop forever, sending key_down events at repeat rate
            while True:
                self._controller.key_down(key, code)
                await asyncio.sleep(self._repeat_rate)
        except asyncio.CancelledError:
            # Task was cancelled (key released) - clean exit
            pass
