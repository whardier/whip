"""macOS input control via pynput.

This module provides the InputController class, which wraps pynput's mouse
and keyboard controllers to provide normalized coordinate-based control of
macOS mouse and keyboard inputs.

Requires Accessibility permissions to function. All operations silently fail
if permissions are not granted.
"""

from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
from Quartz import CGMainDisplayID, CGDisplayPixelsWide, CGDisplayPixelsHigh  # type: ignore[reportAttributeAccessIssue]


class InputController:
    """Controller for mouse and keyboard input on macOS.

    Converts normalized coordinates (0.0-1.0 range) to absolute screen pixels
    and provides methods for mouse movement, clicking, and keyboard input.
    Screen dimensions are cached at initialization for performance.
    """

    def __init__(self) -> None:
        """Initialize controller and cache screen dimensions."""
        self._mouse = MouseController()
        self._keyboard = KeyboardController()

        # Cache screen dimensions
        main_display = CGMainDisplayID()
        self._screen_width = CGDisplayPixelsWide(main_display)
        self._screen_height = CGDisplayPixelsHigh(main_display)

    def move_mouse(self, norm_x: float, norm_y: float) -> None:
        """Move mouse to normalized coordinates.

        Args:
            norm_x: Normalized X coordinate (0.0 = left edge, 1.0 = right edge)
            norm_y: Normalized Y coordinate (0.0 = top edge, 1.0 = bottom edge)
        """
        # Convert normalized coordinates to absolute pixels
        x = int(norm_x * self._screen_width)
        y = int(norm_y * self._screen_height)

        # Clamp to screen bounds
        x = max(0, min(x, self._screen_width - 1))
        y = max(0, min(y, self._screen_height - 1))

        # Set mouse position
        self._mouse.position = (x, y)

    def click(self, button: str, x: float, y: float) -> None:
        """Perform a single click at the specified normalized coordinates.

        Args:
            button: Button to click ("left", "right", or "middle")
            x: Normalized X coordinate (0.0-1.0)
            y: Normalized Y coordinate (0.0-1.0)
        """
        # Move to position first
        self.move_mouse(x, y)

        # Map button string to pynput Button
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }

        pynput_button = button_map.get(button, Button.left)

        # Perform single click
        self._mouse.click(pynput_button, 1)

    def mouse_down(self, button: str, x: float, y: float) -> None:
        """Press mouse button down at the specified normalized coordinates.

        Args:
            button: Button to press ("left", "right", or "middle")
            x: Normalized X coordinate (0.0-1.0)
            y: Normalized Y coordinate (0.0-1.0)
        """
        # Move to position first
        self.move_mouse(x, y)

        # Map button string to pynput Button
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }

        pynput_button = button_map.get(button, Button.left)

        # Press button
        self._mouse.press(pynput_button)

    def mouse_up(self, button: str, x: float, y: float) -> None:
        """Release mouse button at the specified normalized coordinates.

        Args:
            button: Button to release ("left", "right", or "middle")
            x: Normalized X coordinate (0.0-1.0)
            y: Normalized Y coordinate (0.0-1.0)
        """
        # Move to position first
        self.move_mouse(x, y)

        # Map button string to pynput Button
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }

        pynput_button = button_map.get(button, Button.left)

        # Release button
        self._mouse.release(pynput_button)

    def key_down(self, key: str, code: str) -> None:
        """Press a keyboard key down.

        Args:
            key: Key character value (e.g., "a", "Enter", "ArrowUp")
            code: Physical key code (e.g., "KeyA", "Enter") - not used,
                  kept for protocol compatibility
        """
        mapped_key = self._map_key(key)
        self._keyboard.press(mapped_key)

    def key_up(self, key: str, code: str) -> None:
        """Release a keyboard key.

        Args:
            key: Key character value (e.g., "a", "Enter", "ArrowUp")
            code: Physical key code (e.g., "KeyA", "Enter") - not used,
                  kept for protocol compatibility
        """
        mapped_key = self._map_key(key)
        self._keyboard.release(mapped_key)

    def _map_key(self, key: str) -> Key | str:
        """Map key string to pynput Key enum or character.

        Args:
            key: Key character value from browser event

        Returns:
            pynput Key enum for special keys, or the character string for regular keys
        """
        # Special keys mapping (only keys that exist in pynput.keyboard.Key)
        special_keys = {
            "Enter": Key.enter,
            "Tab": Key.tab,
            "Escape": Key.esc,
            "Backspace": Key.backspace,
            "Delete": Key.delete,
            " ": Key.space,
            # Arrow keys
            "ArrowUp": Key.up,
            "ArrowDown": Key.down,
            "ArrowLeft": Key.left,
            "ArrowRight": Key.right,
            # Modifier keys
            "Shift": Key.shift,
            "ShiftLeft": Key.shift_l,
            "ShiftRight": Key.shift_r,
            "Control": Key.ctrl,
            "ControlLeft": Key.ctrl_l,
            "ControlRight": Key.ctrl_r,
            "Alt": Key.alt,
            "AltLeft": Key.alt_l,
            "AltRight": Key.alt_r,
            "Meta": Key.cmd,
            "MetaLeft": Key.cmd_l,
            "MetaRight": Key.cmd_r,
            # Function keys
            "F1": Key.f1,
            "F2": Key.f2,
            "F3": Key.f3,
            "F4": Key.f4,
            "F5": Key.f5,
            "F6": Key.f6,
            "F7": Key.f7,
            "F8": Key.f8,
            "F9": Key.f9,
            "F10": Key.f10,
            "F11": Key.f11,
            "F12": Key.f12,
            # Other special keys (only those supported by pynput)
            "Home": Key.home,
            "End": Key.end,
            "PageUp": Key.page_up,
            "PageDown": Key.page_down,
            # Note: Insert and CapsLock not in pynput.Key enum
        }

        # Return mapped special key if found, otherwise return character as-is
        return special_keys.get(key, key)
