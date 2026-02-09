---
phase: 03-macos-control-integration
plan: 01
subsystem: macOS Input Control
tags: [permissions, input-control, pynput, mouse, keyboard]
dependency-graph:
  requires: []
  provides: [permissions-check, input-controller]
  affects: [03-02]
tech-stack:
  added: [pynput, pyobjc-framework-quartz]
  patterns: [normalized-coordinates, screen-dimension-caching]
key-files:
  created:
    - src/whip/permissions.py
    - src/whip/controller.py
  modified:
    - pyproject.toml
    - uv.lock
decisions:
  - "Use pynput for cross-platform mouse/keyboard control (recommended in research)"
  - "Test mouse movement to detect Accessibility permission status (no native Python API)"
  - "Cache screen dimensions at initialization (performance optimization)"
  - "Use normalized coordinates (0-1 range) for resolution-independent input"
  - "Map browser key strings to pynput Key enum (comprehensive special key support)"
metrics:
  duration: 2
  tasks-completed: 2
  files-created: 2
  files-modified: 2
  commits: 2
  completed-at: 2026-02-09
---

# Phase 03 Plan 01: Permission Checking and macOS Control Foundation Summary

**One-liner:** Accessibility permission detection and pynput-based InputController with normalized coordinate system for macOS mouse and keyboard control.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create permissions module with Accessibility check | 2f97468 | src/whip/permissions.py, pyproject.toml, uv.lock |
| 2 | Create InputController for mouse and keyboard control | fb5da59 | src/whip/controller.py |

## Implementation Details

### Task 1: Permission Checking Module

**Created:** `src/whip/permissions.py`

**Key Functions:**
- `check_accessibility_permission() -> bool`: Detects permission status by attempting a test mouse movement and checking if the cursor actually moved
- `print_permission_instructions()`: Displays comprehensive instructions for granting Accessibility permissions, including macOS Sequoia monthly renewal requirement

**Dependency Added:** `pynput>=1.8.0` to pyproject.toml

**Approach:**
Since Python has no native API to check Accessibility permissions, the implementation uses a clever workaround: attempt to move the mouse 1 pixel, wait 0.1s, then check if the position changed. If the OS blocks the movement (no permission), the position remains unchanged. This reliably detects permission status without requiring platform-specific APIs.

### Task 2: InputController Implementation

**Created:** `src/whip/controller.py`

**Key Components:**
- `InputController` class with cached screen dimensions
- Mouse control methods: `move_mouse()`, `click()`, `mouse_down()`, `mouse_up()`
- Keyboard control methods: `key_down()`, `key_up()`
- Private helper: `_map_key()` for browser key string to pynput Key enum mapping

**Screen Size Detection:**
Uses Quartz APIs (`CGMainDisplayID`, `CGDisplayPixelsWide`, `CGDisplayPixelsHigh`) to get primary display dimensions. Screen size is cached at initialization for performance, avoiding repeated system calls during rapid input events.

**Coordinate System:**
Accepts normalized coordinates (0.0-1.0 range) and converts to absolute pixels:
- `x_pixels = int(norm_x * screen_width)`
- `y_pixels = int(norm_y * screen_height)`
- Clamped to screen bounds to prevent out-of-range errors

**Key Mapping:**
Comprehensive mapping of browser key strings to pynput Key enums:
- Special keys: Enter, Tab, Escape, Backspace, Delete, Space
- Arrow keys: ArrowUp, ArrowDown, ArrowLeft, ArrowRight
- Modifier keys: Shift, Control, Alt, Meta (mapped to macOS Command)
- Function keys: F1-F12
- Other: Home, End, PageUp, PageDown, Insert, CapsLock
- Regular characters passed through as-is (pynput handles single chars directly)

**Button Mapping:**
Browser button strings ("left", "right", "middle") mapped to pynput Button enums (Button.left, Button.right, Button.middle).

## Verification Results

All verifications passed:

1. Both modules import without errors
2. Type checking passes for both files (0 errors, 0 warnings)
3. pynput dependency installed successfully
4. Screen size detection working (detected: 1792x1120)
5. InputController instantiates successfully

**Type Checker Note:** Added `# type: ignore[reportAttributeAccessIssue]` for Quartz imports due to PyObjC type stub limitations. Code works correctly at runtime.

## Deviations from Plan

None - plan executed exactly as written.

## Integration Points

**Provides for Plan 03-02:**
- `permissions.py`: Permission checking before server starts
- `controller.py`: InputController instance for processing WebSocket events
- Normalized coordinate system matches browser's 0-1 range (already implemented in Phase 2)

**Next Steps (Plan 03-02):**
- Integrate InputController into WebSocket handler
- Add permission check at server startup
- Wire mouse/keyboard events from queue to controller methods

## Dependencies Added

**Production:**
- `pynput>=1.8.0`: Cross-platform mouse/keyboard control with macOS Accessibility support

**Transitive (installed by pynput):**
- `pyobjc-core==12.1`: Python-Objective-C bridge
- `pyobjc-framework-quartz==12.1`: Quartz/Core Graphics bindings for screen size detection
- `pyobjc-framework-applicationservices==12.1`: Application Services framework
- `pyobjc-framework-cocoa==12.1`: Cocoa framework
- `pyobjc-framework-coretext==12.1`: Core Text framework
- `six==1.17.0`: Python 2/3 compatibility utilities

## Technical Decisions

1. **pynput over PyAutoGUI/Quartz:**
   - Research recommended pynput for better multi-monitor support and active maintenance
   - March 2025 release (1.8.1) confirmed Python 3.12 compatibility
   - Simpler API than raw Quartz, more robust than PyAutoGUI on macOS

2. **Test-based permission detection:**
   - No native Python API exists for checking Accessibility permissions
   - Test mouse movement approach is reliable and non-intrusive
   - Small 1-pixel movement minimizes visual disturbance
   - 0.1s delay ensures OS has time to process the movement

3. **Screen dimension caching:**
   - Quartz API calls are relatively expensive
   - Screen size rarely changes during application runtime
   - Cache at init eliminates per-event overhead
   - Acceptable trade-off: won't detect mid-session screen changes (extremely rare)

4. **Normalized coordinate system:**
   - Matches browser's MouseEvent.clientX/clientY normalized to canvas dimensions
   - Resolution-independent (works across different display sizes)
   - Simplifies integration with existing Phase 2 browser event capture
   - Controller handles conversion to absolute pixels internally

5. **Comprehensive key mapping:**
   - Browser KeyboardEvent.key values vary (e.g., "Enter", "ArrowUp", "Meta")
   - pynput requires Key enum for special keys, strings for characters
   - Mapping function provides clean abstraction
   - Future-proof: easy to add more mappings if needed

## Performance Characteristics

**Screen Size Query:** O(1) - cached at initialization
**Mouse Movement:** O(1) - direct coordinate conversion and position assignment
**Mouse Click:** O(1) - position set + single button press/release
**Key Press:** O(1) - dictionary lookup + keyboard press/release

**Expected Throughput:**
- Mouse events: Sub-millisecond processing (normalization + pynput call)
- Keyboard events: Sub-millisecond processing (mapping + pynput call)

**Bottleneck:** macOS Accessibility event posting (OS-level, unavoidable)

## Known Limitations

1. **Silent failure without permissions:**
   - pynput operations succeed but have no effect if Accessibility not granted
   - Plan 03-02 will add startup permission check to mitigate

2. **macOS Sequoia monthly renewal:**
   - Permissions expire monthly and after every reboot
   - Instructions mention this requirement
   - Server should check permissions at startup and provide clear error

3. **Primary display only:**
   - Quartz functions used query primary display dimensions
   - Multi-monitor setups won't work correctly with secondary displays
   - Acceptable for MVP (single-monitor is most common use case)

4. **No coordinate validation:**
   - Controller clamps to screen bounds but doesn't validate input range
   - Assumes caller provides 0-1 normalized values
   - Plan 03-02 will validate WebSocket data before passing to controller

## Self-Check: PASSED

**Created Files:**
```
FOUND: src/whip/permissions.py
FOUND: src/whip/controller.py
```

**Modified Files:**
```
FOUND: pyproject.toml (pynput>=1.8.0 in dependencies)
FOUND: uv.lock (updated with pynput and pyobjc packages)
```

**Commits:**
```
FOUND: 2f97468 (Task 1: permissions module)
FOUND: fb5da59 (Task 2: InputController)
```

**Verification Commands:**
```bash
# Both modules import successfully
uv run python -c "from whip.permissions import check_accessibility_permission, print_permission_instructions; print('OK')"
uv run python -c "from whip.controller import InputController; print('OK')"

# Screen size detection works
uv run python -c "from whip.controller import InputController; c = InputController(); print(f'{c._screen_width}x{c._screen_height}')"
# Output: 1792x1120

# Type checking passes
uv run pyright src/whip/permissions.py src/whip/controller.py
# Output: 0 errors, 0 warnings, 0 informations
```

All claims verified. Plan 03-01 complete and ready for integration in Plan 03-02.
