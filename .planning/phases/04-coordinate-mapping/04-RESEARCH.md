# Phase 4: Coordinate Mapping - Research

**Researched:** 2026-02-09
**Domain:** macOS coordinate systems, HiDPI/Retina display handling, keyboard repeat implementation
**Confidence:** MEDIUM-HIGH

## Summary

Phase 4 addresses two distinct areas: coordinate mapping accuracy across Retina/HiDPI displays and multi-monitor setups, and keyboard repeat functionality. The research reveals critical nuances in macOS coordinate systems - notably that CGDisplayPixelsWide/High return **points, not pixels** despite their names, requiring careful handling for Retina displays. The current implementation already uses normalized coordinates (0-1 range), which is the correct approach, but verification and edge case handling are needed. For keyboard repeat, the frontend currently filters all repeat events (`if (e.repeat) return;`), requiring a server-side timer-based implementation for proper key repeat behavior.

**Primary recommendation:** Verify that CGDisplayPixelsWide/High work correctly with pynput's point-based coordinate system (they should, as both use points), add corner-case testing, implement server-side keyboard repeat using asyncio timers with configurable delay and rate, and consider multi-monitor boundary validation.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pynput | 1.7.6+ | macOS input control | Cross-platform, uses native Quartz events, handles point/pixel abstraction |
| pyobjc-framework-Quartz | Latest | Screen info via Quartz | Official macOS framework bindings, provides CGDisplay* functions |
| asyncio | stdlib | Keyboard repeat timing | Python standard library, non-blocking timers, integrates with existing event loop |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mss | 6+ (optional) | Multi-monitor bounds | If multi-monitor support added, provides accurate display boundaries |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pynput | Direct Quartz CGEvent | More control but much more complex, loses cross-platform support |
| asyncio timers | threading.Timer | Simpler but blocks and doesn't integrate with existing event loop |
| CGDisplayPixelsWide/High | NSScreen backingScaleFactor | More accurate but requires Objective-C bridge, overkill for single display |

**Installation:**
```bash
# Already installed in Phase 3
# pynput and pyobjc-framework-Quartz are existing dependencies
```

## Architecture Patterns

### Coordinate System Flow
```
Browser Canvas                 WebSocket              Server
---------------               ----------              ------
CSS pixels (e.offsetX)   →    Normalized       →     macOS points
÷ canvas.width               (0.0 - 1.0)            × screen_width
= normalized x                5 decimal places       = absolute x

canvas: 1920 CSS px      →    0.50000          →     1280 points
= 960 CSS px                                         (on 2560pt display)
```

### Pattern 1: Points vs Pixels Distinction
**What:** macOS uses "points" (logical coordinates) not "pixels" (physical) for screen coordinates
**When to use:** All coordinate calculations on macOS
**Example:**
```python
# Source: https://github.com/lionheart/openradar-mirror/issues/18671
# CGDisplayPixelsWide/High return POINTS despite the name
main_display = CGMainDisplayID()
screen_width = CGDisplayPixelsWide(main_display)   # Returns points, not pixels!
screen_height = CGDisplayPixelsHigh(main_display)  # Returns points, not pixels!

# On Retina 2x display:
# Physical pixels: 5120 × 2880
# Points (what CGDisplay* returns): 2560 × 1440
# This is CORRECT - pynput also uses points
```

### Pattern 2: Normalized Coordinate Mapping
**What:** Browser sends 0-1 range coordinates, server multiplies by screen dimensions
**When to use:** All mouse position calculations
**Example:**
```python
# Already implemented correctly in controller.py
def move_mouse(self, norm_x: float, norm_y: float) -> None:
    # Convert normalized coordinates to absolute points
    x = int(norm_x * self._screen_width)   # screen_width is in points
    y = int(norm_y * self._screen_height)  # screen_height is in points

    # Clamp to screen bounds
    x = max(0, min(x, self._screen_width - 1))
    y = max(0, min(y, self._screen_height - 1))

    # pynput expects points, which matches CGDisplay* output
    self._mouse.position = (x, y)
```

### Pattern 3: Keyboard Repeat with Asyncio Timer
**What:** Server-side key repeat using asyncio tasks, not OS auto-repeat
**When to use:** When key held down, after initial delay
**Example:**
```python
# Conceptual pattern - needs integration with existing code
import asyncio

class KeyRepeatManager:
    def __init__(self):
        self._repeat_tasks = {}  # key -> asyncio.Task
        self._repeat_delay = 0.5  # Initial delay in seconds
        self._repeat_rate = 0.033  # 30 times per second

    async def _repeat_key(self, key: str, code: str):
        """Background task that repeats a key press."""
        await asyncio.sleep(self._repeat_delay)  # Initial delay

        while True:
            # Send key_down event to InputController
            await self._send_key_event(key, code)
            await asyncio.sleep(self._repeat_rate)

    def start_repeat(self, key: str, code: str):
        """Start repeating a key."""
        if key not in self._repeat_tasks:
            task = asyncio.create_task(self._repeat_key(key, code))
            self._repeat_tasks[key] = task

    def stop_repeat(self, key: str):
        """Stop repeating a key."""
        if key in self._repeat_tasks:
            self._repeat_tasks[key].cancel()
            del self._repeat_tasks[key]
```

### Pattern 4: Corner Validation Testing
**What:** Test that normalized coordinates 0,0 and 1,1 map to actual screen corners
**When to use:** Verification step after coordinate mapping changes
**Example:**
```python
# Verification pattern (not production code)
def verify_corner_mapping():
    """Test corner coordinates map correctly."""
    test_cases = [
        (0.0, 0.0, "top-left"),
        (1.0, 0.0, "top-right"),
        (0.0, 1.0, "bottom-left"),
        (1.0, 1.0, "bottom-right"),
        (0.5, 0.5, "center"),
    ]

    for norm_x, norm_y, label in test_cases:
        controller.move_mouse(norm_x, norm_y)
        actual_pos = controller._mouse.position
        expected_x = int(norm_x * screen_width)
        expected_y = int(norm_y * screen_height)
        print(f"{label}: expected ({expected_x}, {expected_y}), got {actual_pos}")
```

### Anti-Patterns to Avoid
- **Using window.devicePixelRatio server-side:** Server doesn't need DPR - normalized coordinates already abstract this away
- **Multiplying by backingScaleFactor:** CGDisplay* and pynput both use points, no scaling needed
- **Filtering repeat events client-side then implementing client-side repeat:** Creates inconsistent timing and duplicated logic
- **Using threading.Timer for keyboard repeat:** Blocks the event loop and doesn't integrate with asyncio

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Screen resolution detection | Custom display queries | CGDisplayPixelsWide/High | Native Quartz API, handles multi-display, already cached |
| Mouse coordinate transformation | Manual point/pixel conversion | pynput + CGDisplay* | Both use points, no conversion needed |
| Keyboard repeat timing | Custom timer thread pool | asyncio.create_task + sleep | Non-blocking, integrates with event loop, easy cancellation |
| Multi-monitor bounds | Screen edge calculation | mss library (if needed) | Handles negative coordinates, multiple origins, tested |

**Key insight:** The current implementation is already correct for single displays. The main work is verification, edge case handling, and adding keyboard repeat - not rewriting coordinate logic.

## Common Pitfalls

### Pitfall 1: Assuming CGDisplayPixelsWide/High Return Pixels
**What goes wrong:** Developer thinks CGDisplayPixelsWide returns 5120 on a Retina display, but it returns 2560 (points)
**Why it happens:** Function names are misleading - they actually return points, not pixels
**How to avoid:** Treat all macOS screen coordinates as "points" (logical units). On 2x Retina, 1 point = 2 pixels, but you never need to think about physical pixels when using pynput + Quartz
**Warning signs:** Cursor appears to move at half speed or only covers half the screen on Retina displays

### Pitfall 2: Multi-Monitor Negative Coordinates
**What goes wrong:** pynput accepts negative coordinates (monitors to the left of primary), but code clamps to 0 minimum
**Why it happens:** Current code assumes single monitor with origin at (0, 0)
**How to avoid:** For multi-monitor support, detect all displays and their origins, don't clamp to 0
**Warning signs:** Can't move cursor to monitors positioned left of the primary display

### Pitfall 3: Browser DevicePixelRatio Confusion
**What goes wrong:** Developer thinks they need to send devicePixelRatio to server or apply it server-side
**Why it happens:** Canvas has two sizes (CSS display size and drawing buffer size), causing confusion
**How to avoid:** Keep canvas.width = canvas.clientWidth (no DPR scaling). Normalized coordinates (0-1) already abstract away DPR. Server never needs to know about DPR
**Warning signs:** Implementing canvas scaling with `canvas.width = canvas.clientWidth * window.devicePixelRatio`

### Pitfall 4: Keyboard Repeat Race Conditions
**What goes wrong:** Multiple repeat tasks start for the same key, causing accelerated repeat or orphaned tasks
**Why it happens:** key_down events arrive while repeat task already running
**How to avoid:** Track active repeat tasks in a dict, check if key already repeating before starting new task
**Warning signs:** Keys repeat faster than expected, memory usage grows during long key holds

### Pitfall 5: asyncio.sleep Precision on Windows
**What goes wrong:** Keyboard repeat timing is imprecise (rounds to 15ms on Windows)
**Why it happens:** Windows timer granularity is 15ms, asyncio.sleep inherits this limitation
**How to avoid:** Accept ~15ms precision on Windows (acceptable for keyboard repeat). For sub-millisecond precision, would need platform-specific timers (not worth complexity)
**Warning signs:** Repeat rate isn't exactly as configured on Windows (but macOS/Linux should be precise)

### Pitfall 6: Integer Truncation at Screen Edges
**What goes wrong:** Coordinate 0.99999 maps to pixel 2559 instead of 2560, cursor doesn't reach far edge
**Why it happens:** `int(0.99999 * 2560) = int(2559.9744) = 2559`
**How to avoid:** Current code clamps to `screen_width - 1`, which is correct. But if changing to rounding, use `min(int(norm_x * screen_width), screen_width - 1)`
**Warning signs:** Can't quite reach the rightmost or bottommost pixel

## Code Examples

Verified patterns from official sources:

### Detecting Screen Resolution (Current Implementation)
```python
# Source: controller.py (already implemented)
from Quartz import CGMainDisplayID, CGDisplayPixelsWide, CGDisplayPixelsHigh

def __init__(self) -> None:
    # Cache screen dimensions (in points, not pixels!)
    main_display = CGMainDisplayID()
    self._screen_width = CGDisplayPixelsWide(main_display)
    self._screen_height = CGDisplayPixelsHigh(main_display)
    # Example: Returns 2560×1440 on Retina MBP (logical points)
```

### JavaScript KeyboardEvent Repeat Detection
```javascript
// Source: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/repeat
canvas.addEventListener('keydown', (e) => {
  if (e.repeat) {
    // This is an auto-repeated keydown event
    // Currently filtered out: if (e.repeat) return;
    // For Phase 4: allow through, or handle server-side
  } else {
    // This is the initial keydown event
  }
});
```

### Browser Normalized Coordinates (Current Implementation)
```javascript
// Source: static/index.html (already implemented)
function roundCoord(value) {
    return Math.round(value * 100000) / 100000;  // 5 decimal precision
}

canvas.addEventListener('mousemove', (e) => {
    const x = roundCoord(e.offsetX / canvas.width);   // 0-1 range
    const y = roundCoord(e.offsetY / canvas.height);  // 0-1 range
    ws.send(JSON.stringify({
        type: 'mouse_move',
        data: { x, y, timestamp: Date.now() }
    }));
});
```

### Asyncio Periodic Task Pattern
```python
# Source: Based on https://github.com/riccardobon/timer and asyncio patterns
async def periodic_task(interval: float, callback, *args):
    """Run callback periodically at interval."""
    while True:
        await asyncio.sleep(interval)
        await callback(*args)

# Cancel with:
task = asyncio.create_task(periodic_task(0.033, send_key, "a", "KeyA"))
# Later:
task.cancel()
```

### Multi-Monitor Detection (If Needed)
```python
# Source: https://github.com/moses-palmer/pynput/issues/350 suggests mss
# Not currently implemented, but pattern for future multi-monitor support
from mss import mss

with mss() as sct:
    for monitor in sct.monitors[1:]:  # Skip monitor 0 (all monitors combined)
        print(f"Monitor: {monitor}")
        # Example output: {'left': -260, 'top': -1080, 'width': 1920, 'height': 1080}
        # Note: negative coordinates for monitors left/above primary
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pixel-based coords | Points (logical coords) | macOS Retina introduction (2012) | 1 point = 1-4 pixels depending on display density |
| OS keyboard repeat | App-controlled repeat | Modern input systems | Apps control timing for consistency across platforms |
| Single display assumption | Multi-monitor APIs | ~2010+ | Negative coordinates, multiple origins |
| Accessibility-only permission | Accessibility + Screen Recording | macOS 10.15+ | Screen recording permission may be needed for some APIs |

**Deprecated/outdated:**
- **Physical pixel coordinates:** macOS APIs work in points since Retina displays
- **Blocking time.sleep for repeat:** asyncio.sleep is non-blocking and integrates with event loop
- **Assuming (0,0) is always top-left:** Multi-monitor setups can have negative coordinates

## Open Questions

1. **Does current implementation work on Retina displays?**
   - What we know: CGDisplay* returns points, pynput uses points - should work
   - What's unclear: Has it been tested? Edge cases at screen boundaries?
   - Recommendation: Create verification test that moves to corners and center, visually confirm

2. **Should keyboard repeat be client-side or server-side?**
   - What we know: Currently filtered client-side (`if (e.repeat) return;`)
   - What's unclear: User preference - OS timing vs. consistent cross-platform timing?
   - Recommendation: Server-side gives consistent behavior and matches remote desktop pattern

3. **Is multi-monitor support needed for MVP?**
   - What we know: Not in original Phase 4 requirements
   - What's unclear: User's actual use case (single laptop screen vs. multi-monitor desktop)
   - Recommendation: Single monitor for Phase 4, multi-monitor for Phase 6 if needed

4. **What should keyboard repeat rate/delay be?**
   - What we know: macOS defaults are configurable per-user
   - What's unclear: Should WHIP match user's macOS settings or use fixed values?
   - Recommendation: Start with fixed reasonable defaults (500ms delay, 30Hz rate), make configurable later

## Sources

### Primary (HIGH confidence)
- Apple Developer Documentation: [CGDisplayPixelsHigh](https://developer.apple.com/documentation/coregraphics/1454247-cgdisplaypixelshigh) - Official API documentation
- GitHub Issue: [CGDisplayPixelsWide/High returns points not pixels](https://github.com/lionheart/openradar-mirror/issues/18671) - Clarifies misleading function names
- MDN Web Docs: [KeyboardEvent.repeat property](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/repeat) - Official web API documentation
- MDN Web Docs: [Window.devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio) - Official web API documentation
- pynput Documentation: [Handling the mouse](https://pynput.readthedocs.io/en/latest/mouse.html) - Official library documentation

### Secondary (MEDIUM confidence)
- GitHub Issue: [pynput multi-screen coordinate system](https://github.com/moses-palmer/pynput/issues/350) - Community-reported issues, maintainer responses
- Apple Developer Archive: [APIs for Supporting High Resolution](https://developer.apple.com/library/archive/documentation/GraphicsAnimation/Conceptual/HighResolutionOSX/APIs/APIs.html) - Official but archived documentation
- WebGL Fundamentals: [Resizing the Canvas](https://webglfundamentals.org/webgl/lessons/webgl-resizing-the-canvas.html) - Community best practices, widely cited
- BetterDisplay Wiki: [macOS Scaling, HiDPI, LoDPI explanation](https://github.com/waydabber/BetterDisplay/wiki/MacOS-scaling,-HiDPI,-LoDPI-explanation) - Community documentation, detailed
- JavaScript.info: [Keyboard: keydown and keyup](https://javascript.info/keyboard-events) - Educational resource, well-maintained

### Tertiary (LOW confidence - needs validation)
- Medium Article: [Apple coordinate system](https://longvudai.medium.com/apple-coordinate-system-cfce33e110b) - Single author, no verification
- R0uter's Blog: [Analyzing multi-monitor window position](https://www.logcg.com/en/archives/2771.html) - Personal blog, useful patterns
- GameDev.net Forums: [Key repeat implementation patterns](https://gamedev.net/forums/topic/556474-repeated-key-down-message/4574005/) - Community discussion, game-focused

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pynput and Quartz are already working in Phase 3, just need verification
- Architecture: MEDIUM-HIGH - Points vs pixels distinction verified by official sources, but edge cases need testing
- Keyboard repeat: MEDIUM - Pattern is well-understood, but integration with existing event consumer needs careful design
- Multi-monitor: LOW - Not thoroughly researched since it's likely out of scope for Phase 4

**Research date:** 2026-02-09
**Valid until:** ~2026-03-09 (30 days - stable domain, macOS APIs change slowly)

**Key unknowns:**
- Actual behavior on user's specific hardware (Retina vs non-Retina)
- Multi-monitor setup in user's environment
- Performance impact of keyboard repeat timers under load
