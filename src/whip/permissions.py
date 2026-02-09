"""macOS Accessibility permission checking and user instructions.

This module provides functions to detect whether the application has been
granted Accessibility permissions on macOS, which are required for
programmatic mouse and keyboard control.

On macOS Sequoia (15.0+), Accessibility permissions must be re-granted
monthly and after every system reboot.
"""

import time
from pynput.mouse import Controller


def check_accessibility_permission() -> bool:
    """Check if Accessibility permission is granted.

    Uses a test mouse movement to detect permission status. If the mouse
    cursor actually moves, permissions are granted. If it doesn't move,
    permissions are denied (the OS silently blocks the operation).

    Returns:
        True if Accessibility permission is granted, False otherwise.
    """
    try:
        mouse = Controller()

        # Get current mouse position
        original_pos = mouse.position

        # Attempt to move mouse 1 pixel
        test_pos = (original_pos[0] + 1, original_pos[1] + 1)
        mouse.position = test_pos

        # Small delay to allow OS to process the movement
        time.sleep(0.1)

        # Check if mouse actually moved
        new_pos = mouse.position

        # Move back to original position
        mouse.position = original_pos

        # If position changed, permissions are granted
        return new_pos != original_pos

    except Exception:
        # Any exception indicates permission denied
        return False


def print_permission_instructions() -> None:
    """Print clear instructions for granting Accessibility permission.

    Displays formatted instructions to help users grant the required
    macOS Accessibility permission to the application running Python.
    """
    print("\n" + "=" * 70)
    print("ACCESSIBILITY PERMISSION REQUIRED")
    print("=" * 70)
    print("\nThis application needs permission to control the mouse and keyboard.")
    print("\nTo grant permission:")
    print("  1. Open System Settings")
    print("  2. Go to Privacy & Security → Accessibility")
    print("  3. Click the lock icon and authenticate")
    print("  4. Enable the application running Python:")
    print("     - Terminal")
    print("     - VS Code")
    print("     - PyCharm")
    print("     - iTerm2")
    print("     - Or whichever app is running this script")
    print("\nIMPORTANT (macOS Sequoia 15.0+):")
    print("  - Accessibility permissions must be re-granted monthly")
    print("  - Permissions reset after every system reboot")
    print("  - You may need to repeat this process periodically")
    print("\nAfter granting permission:")
    print("  - Restart this server/application")
    print("=" * 70)
    print()
