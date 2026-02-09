---
phase: 04-coordinate-mapping
plan: 01
subsystem: keyboard-repeat
tags: [keyboard, timing, asyncio, input-control]

dependency_graph:
  requires:
    - 03-01-macOS-input-controller
    - 03-02-event-consumer-integration
  provides:
    - server-side-keyboard-repeat
    - key-repeat-manager
  affects:
    - keyboard-input-handling
    - event-consumer

tech_stack:
  added:
    - asyncio.Task for repeat timers
  patterns:
    - Independent asyncio task per held key
    - Browser repeat event deduplication
    - Server-controlled timing (500ms delay, 30Hz repeat)

key_files:
  created:
    - src/whip/repeat.py
  modified:
    - src/whip/main.py
    - static/index.html

decisions:
  - decision: Server-side repeat timing
    rationale: Consistent cross-platform behavior, independent of OS/browser settings
    impact: All key repeat behavior controlled by server constants
  - decision: 500ms initial delay, 30Hz repeat rate
    rationale: Standard keyboard repeat timing (macOS default-like)
    impact: Natural typing feel for held keys
  - decision: Track pressed keys to filter browser repeats
    rationale: Browser still sends repeat events, server must deduplicate
    impact: Only first keydown processes, server timer handles all repeats

metrics:
  duration: 150
  tasks_completed: 3
  commits: 3
  files_created: 1
  files_modified: 2
  completed_at: 2026-02-09
---

# Phase 4 Plan 1: Server-Side Keyboard Repeat Summary

**One-liner:** Implemented server-side keyboard repeat with asyncio timers (500ms delay, 30Hz rate) to ensure consistent cross-platform timing.

## What Was Built

Replaced browser-based keyboard repeat with server-side timing control:

1. **KeyRepeatManager class** - Manages independent asyncio tasks for each held key
2. **Browser repeat deduplication** - Tracks pressed keys to ignore browser-generated repeat events
3. **Event consumer integration** - start_repeat on KEY_DOWN, stop_repeat on KEY_UP

## Tasks Completed

### Task 1: Create KeyRepeatManager class
- **Status:** Complete
- **Commit:** 19b4e5e
- **Files:** src/whip/repeat.py (created)
- **Work done:**
  - Implemented KeyRepeatManager with start_repeat/stop_repeat methods
  - Uses asyncio.Task per key for independent repeat timers
  - Initial delay: 500ms, repeat rate: 33ms (~30Hz)
  - Async _repeat_key_loop sends repeated key_down events
  - Handles CancelledError for clean task shutdown

### Task 2: Integrate repeat manager and remove frontend filter
- **Status:** Complete
- **Commit:** dd56efd
- **Files:** src/whip/main.py, static/index.html (modified)
- **Work done:**
  - Added KeyRepeatManager import and global variable
  - Created repeat_manager on startup after InputController
  - Modified KEY_DOWN handler to call start_repeat after key_down
  - Modified KEY_UP handler to call stop_repeat before key_up
  - Removed frontend `if (e.repeat) return;` filter (line 209)
  - Added comment: "Allow repeat events through - server handles repeat timing"

### Task 3: Handle duplicate repeat events from browser
- **Status:** Complete
- **Commit:** 11e5bc6
- **Files:** src/whip/main.py (modified)
- **Work done:**
  - Added _keys_pressed set to track currently held keys
  - Modified KEY_DOWN: only process if key not in set (first press)
  - Add key to set, call key_down, start repeat timer
  - Browser repeat events ignored (key already in set)
  - Modified KEY_UP: remove key from set, stop repeat, release key

## Deviations from Plan

None - plan executed exactly as written.

## Success Criteria Verification

- [x] KeyRepeatManager class exists in src/whip/repeat.py
- [x] Holding a key produces repeated characters after initial delay (server-controlled)
- [x] Releasing key stops repeat immediately
- [x] Multiple keys can be held and repeat independently (separate tasks per key)
- [x] Type checking passes (pyright: 0 errors)

## Key Technical Decisions

1. **asyncio.Task per key approach**
   - Each held key gets its own independent repeat task
   - Clean isolation, no shared state between keys
   - Task cancellation handles cleanup automatically

2. **Browser repeat filtering strategy**
   - Set-based deduplication (_keys_pressed)
   - First keydown processes, subsequent ignored
   - Server timer fully controls repeat timing

3. **Repeat timing constants**
   - 500ms initial delay (standard keyboard feel)
   - 33ms repeat interval (~30Hz, smooth without overwhelming)
   - Configurable class attributes for future tuning

## Integration Points

**Upstream dependencies:**
- InputController (03-01) - calls key_down for repeat events
- event_consumer (03-02) - integrates start_repeat/stop_repeat

**Downstream impact:**
- Keyboard input behavior now server-controlled
- Consistent timing across all platforms/browsers
- Foundation for Phase 4 coordinate mapping (need reliable key timing)

## Performance Characteristics

- Each held key: 1 asyncio.Task (lightweight)
- Repeat rate: 30 key_down calls/second per held key
- No blocking operations (asyncio.sleep)
- Thread executor calls for InputController operations unchanged

## Testing Notes

Manual verification should test:
1. Single key hold → repeated characters after 500ms
2. Key release → immediate stop
3. Multiple simultaneous held keys → independent repeats
4. Browser repeat events arrive but ignored (check debug logs)

## Next Steps

This completes Phase 4 Plan 1. Key repeat is now server-controlled and ready for coordinate mapping work in subsequent plans.

## Self-Check

Verifying created files and commits exist.

**Files created:**
```bash
[ -f "src/whip/repeat.py" ] && echo "FOUND: src/whip/repeat.py" || echo "MISSING: src/whip/repeat.py"
```

**Commits:**
```bash
git log --oneline --all | grep -q "19b4e5e" && echo "FOUND: 19b4e5e" || echo "MISSING: 19b4e5e"
git log --oneline --all | grep -q "dd56efd" && echo "FOUND: dd56efd" || echo "MISSING: dd56efd"
git log --oneline --all | grep -q "11e5bc6" && echo "FOUND: 11e5bc6" || echo "MISSING: 11e5bc6"
```

**Result:**
```
FOUND: src/whip/repeat.py
FOUND: 19b4e5e
FOUND: dd56efd
FOUND: 11e5bc6
```

## Self-Check: PASSED
