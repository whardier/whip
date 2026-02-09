---
phase: 02-browser-input-capture
plan: 02
subsystem: frontend
tags: [keyboard-input, event-prevention, input-capture, real-time, websocket-client]

dependency_graph:
  requires: [canvas-interface, mouse-capture, normalized-coordinates]
  provides: [keyboard-capture, default-behavior-prevention, complete-input-surface]
  affects: [phase-03-macos-control]

tech_stack:
  added:
    - Keyboard event listeners (keydown, keyup)
    - Event.preventDefault() for browser behavior control
    - Auto-repeat filtering (e.repeat check)
  patterns:
    - Browser shortcut preservation (Ctrl/Cmd passthrough)
    - Navigation key prevention (arrows, spacebar, Tab, Page keys)
    - Context menu and selection prevention
    - Auto-focus management for keyboard readiness

key_files:
  created: []
  modified:
    - static/index.html (added keyboard capture and default behavior prevention)

decisions:
  - choice: "Filter auto-repeat events (e.repeat)"
    rationale: "Phase 3 macOS control will handle key release timing. Auto-repeat should be intentional, not automatic browser behavior."
    alternatives: ["Allow auto-repeat", "Server-side filtering"]
  - choice: "Preserve browser shortcuts (skip Ctrl/Cmd keys)"
    rationale: "Users need Ctrl+R for refresh, Ctrl+C for debugging. Browser shortcuts are essential for development and debugging."
    alternatives: ["Capture all keys", "Whitelist specific shortcuts"]
  - choice: "Prevent navigation keys (arrows, spacebar, Tab, Page keys)"
    rationale: "Canvas is the input surface. Scrolling and focus changes would break the capture experience."
    alternatives: ["Allow scrolling", "Capture but don't prevent"]
  - choice: "Auto-focus canvas on WebSocket connection"
    rationale: "Keyboard events work immediately without requiring user to click canvas first."
    alternatives: ["Require click to focus", "Focus on page load"]

metrics:
  duration_minutes: 24
  tasks_completed: 3
  commits: 2
  files_created: 0
  files_modified: 1
  completed_date: "2026-02-09"
---

# Phase 2 Plan 02: Keyboard Input Capture and Browser Behavior Prevention Summary

**Keyboard event capture (key/code) with auto-repeat filtering, default behavior prevention (context menu, scrolling, selection), and browser shortcut preservation for complete input capture surface.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-02-09T21:25:36Z
- **Completed:** 2026-02-09T21:49:08Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 1

## Accomplishments

- Complete keyboard event capture with key and code properties matching protocol.py KeyData spec
- Default browser behaviors prevented (context menu, text selection, scrolling, auto-scroll)
- Navigation keys captured without interfering with browser functionality
- All Phase 2 requirements met and verified by user (full input capture surface operational)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add keyboard event capture** - `b0add5e` (feat)
2. **Task 2: Prevent default browser behaviors** - `26bcbdf` (feat)
3. **Task 3: Verify complete input capture** - Human checkpoint (approved)

## What Was Built

### Task 1: Keyboard Event Capture

Implemented keydown and keyup event listeners on the canvas element that send events to the server via WebSocket. Each event includes both `key` (character value like "a", "Enter", "ArrowUp") and `code` (physical key position like "KeyA", "Enter", "ArrowUp") properties to support both text input and game controls in Phase 3.

**Key features:**
- Auto-repeat filtering: `e.repeat` check prevents multiple key_down events when holding a key
- Auto-focus: Canvas focuses automatically on WebSocket connection for immediate keyboard input
- Protocol compliance: Event structure matches KeyData from protocol.py

**Event format sent to server:**
```javascript
// Key down
{type: "key_down", data: {key: "a", code: "KeyA"}}

// Key up
{type: "key_up", data: {key: "a", code: "KeyA"}}
```

### Task 2: Default Behavior Prevention

Added comprehensive event prevention to create a clean input capture surface without browser interference:

1. **Context menu prevention:** Right-click on canvas no longer shows context menu
2. **Text selection prevention:** Clicking and dragging doesn't select text or show selection cursor
3. **Middle-click auto-scroll prevention:** Middle button doesn't activate auto-scroll mode
4. **Navigation key prevention:** Arrow keys, spacebar, Tab, Home, End, PageUp, PageDown don't scroll or change focus
5. **Browser shortcut preservation:** Ctrl/Cmd+key combinations still work (refresh, copy, paste, devtools)

**Implementation approach:**
- `e.preventDefault()` in mousedown prevents selection and auto-scroll
- `e.preventDefault()` in contextmenu prevents right-click menu
- Conditional prevention in keydown: prevent navigation keys, allow browser shortcuts
- Browser shortcut detection: Skip capture if `e.ctrlKey || e.metaKey` is true

### Task 3: Human Verification (Checkpoint)

User verified complete Phase 2 input capture surface:
- Canvas fills entire viewport with no scrollbars
- Mouse movements captured with normalized coordinates (0-1 range)
- All mouse buttons work (left/right/middle) without browser interference
- Keyboard events captured and transmitted to server
- No context menu on right-click
- No text selection on drag
- No scrolling on arrow keys or spacebar
- Browser shortcuts (Ctrl+R, Cmd+R) still functional
- Connection status indicator shows green "Connected" state

**Verification outcome:** APPROVED - All Phase 2 requirements working correctly

## Files Created/Modified

- `static/index.html` - Added keyboard event listeners (keydown/keyup), default behavior prevention (contextmenu, preventDefault in mousedown/keydown), auto-focus on connection, browser shortcut preservation

## Decisions Made

**1. Auto-repeat filtering**
- Skip key_down events with `e.repeat = true`
- Rationale: Phase 3 macOS control will handle key timing based on actual key releases. Auto-repeat should be intentional, not automatic browser behavior.
- Impact: Single key_down per physical key press, consistent with macOS keyboard behavior

**2. Browser shortcut preservation**
- Skip keyboard capture when Ctrl or Cmd modifier is pressed
- Rationale: Developers need Ctrl+R to refresh, Ctrl+C for debugging, browser devtools access
- Impact: Browser shortcuts work normally while still capturing game controls and text input

**3. Navigation key prevention**
- Prevent default for arrow keys, spacebar, Tab, Page keys
- Rationale: Canvas is the input surface. Scrolling would break the experience (no scrollable content exists).
- Impact: All navigation keys captured without page interference, focus stays on canvas

**4. Auto-focus on connection**
- Canvas.focus() called in WebSocket onopen handler
- Rationale: Keyboard events work immediately without user needing to click canvas first
- Impact: Better UX - page load → connection → immediate keyboard input readiness

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without issues. The plan was comprehensive and all implementations worked as specified.

## Verification Results

All Phase 2 success criteria met (from ROADMAP.md):

1. [x] Blank canvas fills entire browser window (Plan 02-01)
2. [x] Canvas captures mouse movements and sends coordinates in real-time (Plan 02-01)
3. [x] Canvas captures left/right/middle mouse clicks and sends button events (Plan 02-01)
4. [x] Canvas captures keyboard presses and sends key codes (Task 1 of this plan)
5. [x] Context menus and text selection are prevented on canvas (Task 2 of this plan)
6. [x] Connection status indicator shows connected/disconnected state (Plan 02-01)

**All FRONT-* requirements satisfied:**
- FRONT-01: Full-screen canvas (Plan 02-01)
- FRONT-02: Mouse movement with normalized coordinates (Plan 02-01)
- FRONT-03: Mouse clicks with button detection (Plan 02-01)
- FRONT-04: Keyboard events with key and code (Task 1)
- FRONT-05: Events sent via WebSocket (Plans 02-01 and 02-02)
- FRONT-06: Default behaviors prevented (Task 2)
- FRONT-07: Connection status indicator (Plan 02-01)

**User verification confirmed:**
- Mouse events working: Movement, left/right/middle clicks, all logged by server
- Keyboard events working: Letter keys, arrow keys, spacebar all captured
- Prevention working: No context menu, no selection, no scrolling
- Browser shortcuts working: Ctrl+R and Cmd+R still refresh page
- Visual appearance correct: Dark canvas, status overlay, crosshair cursor

## Technical Notes

### Keyboard Event Properties

**Why send both key and code:**
- `key`: Character value, affected by keyboard layout ("a" on QWERTY, "q" on AZERTY)
- `code`: Physical key position, layout-independent ("KeyA" on both layouts)
- Text input use case: Use `key` (user expects layout-specific characters)
- Game control use case: Use `code` (WASD should work regardless of layout)
- Phase 3 macOS control can choose which to use based on context

**Auto-repeat behavior:**
- Browser fires keydown repeatedly when key is held (e.repeat = true)
- We filter these to send only ONE key_down per physical press
- Key release timing controlled by keyup event (user releases key)
- Phase 3 can implement intentional repeat if needed (e.g., hold arrow to keep moving)

### Default Behavior Prevention

**Event.preventDefault() placement:**
- Must call BEFORE browser processes the event
- mousedown: Prevents selection start and auto-scroll setup
- contextmenu: Prevents right-click menu display
- keydown: Prevents navigation actions (scrolling, tab focus change)

**Browser shortcut detection:**
```javascript
if (e.ctrlKey || e.metaKey) {
  return; // Let browser handle
}
```
- `ctrlKey`: Ctrl on Windows/Linux
- `metaKey`: Cmd on macOS
- Early return skips both preventDefault and WebSocket send
- Ensures Ctrl+R (refresh), Ctrl+C (copy), Cmd+Shift+I (devtools) still work

### Focus Management

**Canvas focus strategy:**
1. tabindex="0" makes canvas focusable (from Plan 02-01)
2. canvas.focus() on WebSocket connection (auto-focus)
3. canvas.focus() on mousedown (refocus after mouse interaction)
4. Keyboard events only fire when canvas has focus

**Why auto-focus on connection:**
- Better UX: No click required to start typing
- Immediate readiness: User sees "Connected" → keyboard works
- Fallback: mousedown still calls focus() if user clicks away then back

### Navigation Key Prevention

**Keys prevented:**
- ArrowUp, ArrowDown, ArrowLeft, ArrowRight (scroll page)
- Space (spacebar - scroll down one page)
- Tab (change focus to next element)
- Home, End (scroll to top/bottom)
- PageUp, PageDown (scroll by page)

**Why prevent these:**
- Canvas is the only UI element (no scrollable content)
- Scrolling would create empty space, break full-screen experience
- Tab changing focus would break keyboard input capture
- All these keys are valid input for Phase 3 (game controls, navigation)

## Next Steps

Phase 2 is now COMPLETE. The browser input capture surface is fully operational and ready for Phase 3.

**Phase 3 requirements:**
- macOS control integration using pynput
- Map normalized coordinates (0-1) to screen pixels (e.g., 1920x1080)
- Translate mouse_move events to macOS cursor movement
- Execute mouse clicks via pynput mouse controller
- Translate keyboard events to macOS key presses

**What Phase 3 will receive:**
- Mouse events: {type: "mouse_move/down/up", data: {x: 0.5, y: 0.75, button: "left"}}
- Keyboard events: {type: "key_down/up", data: {key: "a", code: "KeyA"}}
- Normalized coordinates ready for screen mapping
- Clean event stream with auto-repeat filtered
- Connection status for robustness

**Phase 2 deliverables:**
- Full-screen canvas input surface
- Complete mouse capture (movement + all buttons)
- Complete keyboard capture (key + code)
- Default behavior prevention (clean capture surface)
- Real-time WebSocket transmission
- Connection status visibility

The browser is now a complete input capture device ready for macOS control.

## Self-Check: PASSED

**Files verification:**
```
FOUND: /Users/spencersr/tmp/whip/static/index.html (modified with keyboard capture and prevention)
```

**Commits verification:**
```
FOUND: b0add5e (Task 1: feat(02-02): add keyboard event capture)
FOUND: 26bcbdf (Task 2: feat(02-02): prevent default browser behaviors)
```

**Code verification:**
```
✓ Keyboard down listener: canvas.addEventListener('keydown', ...)
✓ Keyboard up listener: canvas.addEventListener('keyup', ...)
✓ Auto-repeat filter: if (e.repeat) return;
✓ Browser shortcut preservation: if (e.ctrlKey || e.metaKey) return;
✓ Navigation key prevention: if ([arrows, space, tab...].includes(e.key)) e.preventDefault();
✓ Context menu prevention: canvas.addEventListener('contextmenu', (e) => e.preventDefault());
✓ Selection prevention: e.preventDefault() in mousedown
✓ Auto-focus: canvas.focus() in ws.onopen
✓ Key/code properties: data: {key: e.key, code: e.code}
```

**User verification:**
```
✓ All Phase 2 requirements verified by user
✓ Mouse events working (movement + all buttons)
✓ Keyboard events working (letters, arrows, spacebar)
✓ Default behaviors prevented (no menu, no selection, no scrolling)
✓ Browser shortcuts working (Ctrl+R, Cmd+R)
✓ Visual appearance correct (dark canvas, status overlay, crosshair)
✓ User response: "approved"
```

All files modified, all commits present, all features working, user verification passed. Phase 2 complete.
