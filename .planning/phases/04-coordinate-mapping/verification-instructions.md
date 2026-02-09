# Coordinate Mapping Verification

## What Was Built

Phase 3 implemented coordinate mapping:
- Browser sends normalized coordinates (0.0-1.0 range) with 5 decimal precision
- Server uses CGDisplayPixelsWide/CGDisplayPixelsHigh to get screen dimensions
- Server multiplies normalized coords by screen dimensions
- pynput moves cursor to absolute position

Research confirms CGDisplayPixelsWide/High return POINTS (not pixels), which matches pynput's coordinate system. This should work correctly on Retina displays without any scaling.

## Prerequisites

1. Start server: `uv run uvicorn whip.main:app --host 0.0.0.0 --port 9447`
2. Open browser to http://localhost:9447
3. Note your screen resolution in the server startup log (e.g., "Screen size: 2560x1440")

## Test 1: Corner Mapping (COORD-05)

Move your mouse to each corner of the canvas and verify the macOS cursor reaches the corresponding screen corner:

| Canvas Position | Expected Screen Position |
|-----------------|-------------------------|
| Top-left corner | Top-left of screen |
| Top-right corner | Top-right of screen |
| Bottom-left corner | Bottom-left of screen |
| Bottom-right corner | Bottom-right of screen |

For each corner: The cursor should be within a few pixels of the actual screen edge/corner.

## Test 2: Center Mapping

Move your mouse to the center of the canvas. The macOS cursor should be near the center of your screen.

## Test 3: Retina Accuracy (COORD-04)

If you're on a Retina/HiDPI display:
- Confirm cursor movements are smooth (not jumping or jittery)
- Confirm clicking on canvas items maps accurately to screen position
- No "half-speed" movement or "only covers half the screen" issues

## Report Template

Reply with verification results:
- Display: [type and resolution]
- Top-left: PASS/FAIL
- Top-right: PASS/FAIL
- Bottom-left: PASS/FAIL
- Bottom-right: PASS/FAIL
- Center: PASS/FAIL
- Issues: [any observed problems, or "none"]
