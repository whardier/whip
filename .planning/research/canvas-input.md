# Canvas Input Capture and Event Handling Research

**Researched:** 2026-02-09
**Confidence:** HIGH

## Executive Summary

Browser canvas elements support comprehensive input handling through standard DOM events. Mouse events (mousemove, mousedown, mouseup) work directly on canvas elements with multiple coordinate systems available. Keyboard events require explicit focus management via tabindex. The modern web platform provides robust APIs for handling different mouse buttons, keyboard input (with key vs code distinction), and touch events. All major browsers fully support these APIs as of 2026.

**Key Recommendation:** Use `offsetX/offsetY` for canvas-relative coordinates, `event.key` for text-like input, `event.code` for physical key positions (games), and add `tabindex="0"` to make canvas keyboard-focusable.

---

## Mouse Event Capture

### Core Mouse Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| `mousedown` | Mouse button pressed | Start dragging, drawing, selection |
| `mouseup` | Mouse button released | End dragging, drawing, selection |
| `mousemove` | Mouse moves over element | Track position, draw while dragging |
| `click` | Full click (down + up) | Simple interactions |
| `dblclick` | Double click | Advanced interactions |
| `contextmenu` | Right-click menu trigger | Custom context menus |

**Source:** [MDN - mousemove event](https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event)

### Basic Implementation Pattern

```javascript
const canvas = document.getElementById('myCanvas');
let isDrawing = false;
let lastX = 0;
let lastY = 0;

canvas.addEventListener('mousedown', (e) => {
  isDrawing = true;
  lastX = e.offsetX;
  lastY = e.offsetY;
});

canvas.addEventListener('mousemove', (e) => {
  if (isDrawing) {
    drawLine(lastX, lastY, e.offsetX, e.offsetY);
    lastX = e.offsetX;
    lastY = e.offsetY;
  }
});

canvas.addEventListener('mouseup', () => {
  isDrawing = false;
});

// Listen on window to catch mouseup outside canvas
window.addEventListener('mouseup', () => {
  isDrawing = false;
});
```

**Sources:**
- [Handling mouse input events for a HTML canvas game](https://stephendoddtech.com/blog/game-design/mouse-event-listener-input-html-canvas)
- [Working with the Mouse | KIRUPA](https://www.kirupa.com/canvas/working_with_the_mouse.htm)

### Performance Considerations

⚠️ **CRITICAL:** `mousemove` fires at very high rates (potentially hundreds of times per second) depending on:
- Mouse movement speed
- CPU performance
- Other running processes

**Mitigation strategies:**
1. Keep event handlers lightweight
2. Defer expensive operations using `requestAnimationFrame()`
3. Throttle or debounce handlers if needed
4. Avoid DOM manipulation inside mousemove handlers

**Source:** [MDN - mousemove event](https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event)

---

## Canvas Coordinate Systems

### Available Coordinate Properties

| Property | Reference Point | Use Case |
|----------|-----------------|----------|
| `offsetX` / `offsetY` | **Target element's padding edge** | **Recommended for canvas** - Direct canvas coordinates |
| `clientX` / `clientY` | Viewport (visible browser window) | UI positioning relative to window |
| `pageX` / `pageY` | Document (includes scroll) | Positioning on scrollable pages |
| `screenX` / `screenY` | Physical screen | Multi-monitor scenarios |
| `movementX` / `movementY` | Previous mousemove event | Delta movement (FPS cameras, pointer lock) |

### Coordinate System Breakdown

**offsetX/offsetY** (RECOMMENDED for canvas):
- Coordinates relative to the element's padding edge
- Always (0, 0) at top-left corner of canvas
- No manual calculations needed
- **Direct canvas pixel coordinates**

**clientX/clientY**:
- Relative to the viewport (visible browser window)
- Does NOT account for page scroll
- Must subtract canvas.getBoundingClientRect() to get canvas coords

**pageX/pageY**:
- Relative to entire document (includes scroll offset)
- Must subtract canvas.offsetLeft + canvas.offsetTop + scroll position
- Useful for scrollable pages

**Sources:**
- [The JavaScript Mouse Event Mystery: clientX, pageX, offsetX Explained](https://medium.com/@greenduckstudiogames/the-javascript-mouse-event-mystery-clientx-pagex-offsetx-explained-eccd8231fc81)
- [MDN - Coordinate systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems)

### Getting Canvas-Relative Coordinates

**Best practice:** Use `offsetX` and `offsetY` directly:

```javascript
canvas.addEventListener('mousemove', (e) => {
  const canvasX = e.offsetX;
  const canvasY = e.offsetY;
  // These are already in canvas coordinate space
});
```

**Alternative (if offsetX unavailable - rare):**

```javascript
function getCanvasCoordinates(canvas, event) {
  const rect = canvas.getBoundingClientRect();
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  };
}
```

**Source:** [Canvas coordinate system](https://g.antv.antgroup.com/en/api/canvas/coordinates)

---

## Mouse Button Detection

### Button Property Values

The `event.button` property identifies which mouse button triggered the event:

| Value | Button | Common Use |
|-------|--------|------------|
| `0` | Left button | Primary interaction, drawing, selection |
| `1` | Middle button | Pan, special actions |
| `2` | Right button | Context menus, alternate actions |

### Implementation Example

```javascript
canvas.addEventListener('mousedown', (e) => {
  if (e.button === 0) {
    // Left click - primary action
    startDrawing(e.offsetX, e.offsetY);
  } else if (e.button === 1) {
    // Middle click - pan
    startPanning(e.offsetX, e.offsetY);
  } else if (e.button === 2) {
    // Right click - context menu or alternate action
    showContextMenu(e.offsetX, e.offsetY);
  }
});
```

### Buttons Bitmask (for mousemove)

The `event.buttons` property is a bitmask showing ALL currently pressed buttons:

| Value | Buttons Pressed |
|-------|----------------|
| `0` | None |
| `1` | Left (bit 0) |
| `2` | Right (bit 1) |
| `4` | Middle (bit 2) |
| `3` | Left + Right |
| `5` | Left + Middle |

```javascript
canvas.addEventListener('mousemove', (e) => {
  if (e.buttons === 1) {
    // Left button held while moving
    draw(e.offsetX, e.offsetY);
  } else if (e.buttons === 4) {
    // Middle button held while moving
    pan(e.offsetX, e.offsetY);
  }
});
```

**Sources:**
- [Working with the Mouse | KIRUPA](https://www.kirupa.com/canvas/working_with_the_mouse.htm)
- [How to detect different mouse button clicks](https://accreditly.io/articles/how-to-detect-different-mouse-button-clicks)

---

## Keyboard Event Handling

### Canvas Focus Requirement

⚠️ **CRITICAL:** Canvas elements do NOT receive keyboard events by default. You MUST make them focusable.

**Solution:** Add `tabindex` attribute:

```html
<canvas id="myCanvas" width="800" height="600" tabindex="0"></canvas>
```

**Tabindex values:**
- `tabindex="0"` - Makes element focusable and includes it in natural tab order (RECOMMENDED)
- `tabindex="-1"` - Focusable programmatically only (via JavaScript)
- `tabindex="1+"` - AVOID - Disrupts natural tab order (accessibility issue)

**Focus management:**

```javascript
const canvas = document.getElementById('myCanvas');

// Give focus when user interacts with canvas
canvas.addEventListener('mousedown', () => {
  canvas.focus();
});

// Or focus on mouseover
canvas.addEventListener('mouseenter', () => {
  canvas.focus();
});
```

**Sources:**
- [Canvas key events](http://www.dbp-consulting.com/tutorials/canvas/CanvasKeyEvents.html)
- [WebAIM: Keyboard Accessibility - Tabindex](https://webaim.org/techniques/keyboard/tabindex)
- [Control focus with tabindex | web.dev](https://web.dev/articles/control-focus-with-tabindex)

### Keyboard Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| `keydown` | Key pressed down | Main event for game controls, shortcuts |
| `keyup` | Key released | Detect key release (stop movement) |
| `keypress` | DEPRECATED | Don't use - use keydown instead |

### event.key vs event.code

**CRITICAL DISTINCTION:**

| Property | Returns | Layout-Aware? | Use Case |
|----------|---------|---------------|----------|
| `event.key` | **Character value** (e.g., "a", "Z", "Enter") | YES | Text input, shortcuts, UI interactions |
| `event.code` | **Physical key position** (e.g., "KeyA", "KeyW") | NO | Game controls, layout-independent bindings |

### When to Use Each

**Use `event.key` for:**
- Text input and form handling
- UI keyboard shortcuts (Ctrl+C, Ctrl+V)
- Language-aware interactions
- Any case where you care about what character the user intended

```javascript
canvas.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    save(); // Ctrl+S works on all keyboard layouts
  }

  if (e.key === 'Escape') {
    cancelOperation();
  }
});
```

**Use `event.code` for:**
- Game controls (WASD movement)
- Physical key position matters
- Layout-independent key bindings
- When you need consistency across keyboard layouts

```javascript
canvas.addEventListener('keydown', (e) => {
  // WASD movement - always same physical keys
  if (e.code === 'KeyW') moveUp();
  if (e.code === 'KeyA') moveLeft();
  if (e.code === 'KeyS') moveDown();
  if (e.code === 'KeyD') moveRight();

  // Spacebar
  if (e.code === 'Space') {
    jump();
  }
});
```

**Sources:**
- [MDN - KeyboardEvent](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)
- [Keyboard: keydown and keyup](https://javascript.info/keyboard-events)
- [Should I use e.code or e.key when handling keyboard events?](https://blog.andri.co/022-should-i-use-ecode-or-ekey-when-handling-keyboard-events/)
- [What's new with KeyboardEvents? Keys and codes!](https://developer.chrome.com/blog/keyboardevent-keys-codes)

### Common Key Values (event.key)

| Key | Value | Key | Value |
|-----|-------|-----|-------|
| Space | `" "` | Enter | `"Enter"` |
| Escape | `"Escape"` | Tab | `"Tab"` |
| Backspace | `"Backspace"` | Delete | `"Delete"` |
| Arrow Up | `"ArrowUp"` | Arrow Down | `"ArrowDown"` |
| Arrow Left | `"ArrowLeft"` | Arrow Right | `"ArrowRight"` |
| Shift | `"Shift"` | Control | `"Control"` |
| Alt | `"Alt"` | Meta | `"Meta"` (Cmd/Win) |

### Common Key Codes (event.code)

| Physical Key | Code | Physical Key | Code |
|--------------|------|--------------|------|
| A key | `"KeyA"` | Space | `"Space"` |
| W key | `"KeyW"` | Enter | `"Enter"` |
| 1 key (top) | `"Digit1"` | 1 (numpad) | `"Numpad1"` |
| Left Arrow | `"ArrowLeft"` | Right Shift | `"ShiftRight"` |

### Modifier Keys

```javascript
canvas.addEventListener('keydown', (e) => {
  if (e.ctrlKey) {
    // Control/Command key is pressed
  }

  if (e.shiftKey) {
    // Shift key is pressed
  }

  if (e.altKey) {
    // Alt/Option key is pressed
  }

  if (e.metaKey) {
    // Meta key (Command on Mac, Windows key on PC) is pressed
  }

  // Combinations
  if (e.ctrlKey && e.shiftKey && e.key === 'Z') {
    redo();
  }
});
```

### Key Repeat Detection

```javascript
canvas.addEventListener('keydown', (e) => {
  if (e.repeat) {
    // Key is being held down (auto-repeat)
    // Ignore if you only want to respond once
    return;
  }

  // First keydown event
  handleKeyPress(e.code);
});
```

**Source:** [MDN - KeyboardEvent](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)

### Deprecated Properties (AVOID)

❌ **DON'T USE:**
- `event.keyCode` - Deprecated, use `key` or `code` instead
- `event.charCode` - Deprecated
- `event.which` - Deprecated

**Source:** [MDN - KeyboardEvent: keyCode property](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/keyCode)

---

## Preventing Default Browser Behaviors

### preventDefault() vs stopPropagation()

| Method | What It Does | When to Use |
|--------|--------------|-------------|
| `event.preventDefault()` | **Cancels default browser action** | Prevent scrolling, context menu, browser shortcuts |
| `event.stopPropagation()` | **Stops event bubbling to parents** | Prevent parent handlers from running |

**Key difference:** `preventDefault()` affects browser behavior, `stopPropagation()` affects event flow through DOM.

**Sources:**
- [MDN - Event: preventDefault() method](https://developer.mozilla.org/en-US/docs/Web/API/Event/preventDefault)
- [MDN - Event: stopPropagation() method](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation)

### Common preventDefault() Use Cases

**1. Prevent context menu (right-click menu):**

```javascript
canvas.addEventListener('contextmenu', (e) => {
  e.preventDefault(); // Disable right-click menu
});
```

**2. Prevent arrow key scrolling:**

```javascript
canvas.addEventListener('keydown', (e) => {
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault(); // Prevent page scroll
  }
});
```

**3. Prevent spacebar scrolling:**

```javascript
canvas.addEventListener('keydown', (e) => {
  if (e.code === 'Space') {
    e.preventDefault(); // Prevent page scroll on space
  }
});
```

**4. Prevent browser shortcuts:**

```javascript
canvas.addEventListener('keydown', (e) => {
  // Prevent Ctrl+S (save page)
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    saveCanvas(); // Your custom save
  }

  // Prevent Ctrl+P (print)
  if (e.ctrlKey && e.key === 'p') {
    e.preventDefault();
  }
});
```

**5. Prevent text selection while dragging:**

```javascript
canvas.addEventListener('mousedown', (e) => {
  e.preventDefault(); // Prevent text selection
});
```

**Sources:**
- [How to Disable Right Click on a Website Using JavaScript](https://coreui.io/blog/how-to-disable-right-click-on-a-website-using-javascript/)
- [MDN - Element: contextmenu event](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event)

### When NOT to Use preventDefault()

❌ **Don't prevent:**
- Tab key (breaks keyboard navigation - accessibility issue)
- Browser refresh (F5) - users expect this to work
- Browser DevTools shortcuts (F12, Ctrl+Shift+I)
- Screen reader shortcuts

---

## Touch Event Handling (Future Extension)

### Core Touch Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| `touchstart` | Finger touches screen | Start gesture, drawing |
| `touchmove` | Finger moves while touching | Track movement, draw |
| `touchend` | Finger lifts from screen | Complete gesture |
| `touchcancel` | Touch interrupted | Clean up (finger wanders off) |

### Touch Event Properties

**TouchEvent:**
- `touches` - All currently active touch points
- `targetTouches` - Touch points on the target element
- `changedTouches` - Touch points that changed

**Touch (single touch point):**
- `identifier` - Unique ID (tracks same finger across events)
- `clientX`, `clientY` - Viewport coordinates
- `pageX`, `pageY` - Document coordinates
- `screenX`, `screenY` - Screen coordinates

### Basic Touch Implementation

```javascript
let isDrawing = false;

canvas.addEventListener('touchstart', (e) => {
  e.preventDefault(); // Prevent scrolling

  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  const x = touch.clientX - rect.left;
  const y = touch.clientY - rect.top;

  isDrawing = true;
  startDrawing(x, y);
});

canvas.addEventListener('touchmove', (e) => {
  e.preventDefault(); // Prevent scrolling

  if (!isDrawing) return;

  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  const x = touch.clientX - rect.left;
  const y = touch.clientY - rect.top;

  draw(x, y);
});

canvas.addEventListener('touchend', (e) => {
  e.preventDefault();
  isDrawing = false;
});
```

**Sources:**
- [MDN - Touch events](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events)
- [Using Touch Events with the HTML5 Canvas](https://bencentra.com/code/2014/12/05/html5-canvas-touch-events.html)
- [HTML5 Canvas Mobile Touch Events Tutorial | Konva](https://konvajs.org/docs/events/Mobile_Events.html)

### Touch vs Mouse Events

⚠️ **CRITICAL:** Calling `preventDefault()` on `touchstart` or the first `touchmove` **prevents corresponding mouse events from firing**.

**Best practice:**
- Call `preventDefault()` on `touchmove` (not `touchstart`) to preserve mouse events
- Or handle both touch and mouse events separately

```javascript
// Unified handler approach
function handlePointerStart(x, y) {
  startDrawing(x, y);
}

// Touch handler
canvas.addEventListener('touchstart', (e) => {
  e.preventDefault();
  const touch = e.touches[0];
  const rect = canvas.getBoundingClientRect();
  handlePointerStart(
    touch.clientX - rect.left,
    touch.clientY - rect.top
  );
});

// Mouse handler
canvas.addEventListener('mousedown', (e) => {
  handlePointerStart(e.offsetX, e.offsetY);
});
```

**Source:** [MDN - Touch events](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events)

### Multi-Touch Support

```javascript
canvas.addEventListener('touchstart', (e) => {
  e.preventDefault();

  // Handle multiple simultaneous touches
  Array.from(e.touches).forEach(touch => {
    console.log(`Touch ${touch.identifier}:`, touch.clientX, touch.clientY);
  });
});

canvas.addEventListener('touchmove', (e) => {
  e.preventDefault();

  // Only process changed touches
  Array.from(e.changedTouches).forEach(touch => {
    updateTouch(touch.identifier, touch.clientX, touch.clientY);
  });
});
```

### Modern Alternative: Pointer Events

**Recommendation:** For new projects, consider using **Pointer Events API** instead of separate mouse/touch handlers:

```javascript
// Pointer Events unify mouse, touch, and pen input
canvas.addEventListener('pointerdown', (e) => {
  startDrawing(e.offsetX, e.offsetY);
});

canvas.addEventListener('pointermove', (e) => {
  if (isDrawing) {
    draw(e.offsetX, e.offsetY);
  }
});

canvas.addEventListener('pointerup', (e) => {
  isDrawing = false;
});
```

**Benefits:**
- Single event handling for mouse, touch, and pen
- Better cross-device support
- Simpler code (no separate touch/mouse handlers)

**Source:** [MDN - Touch events](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events) (recommends Pointer Events)

---

## Complete Input Handling Example

```javascript
const canvas = document.getElementById('myCanvas');
const ctx = canvas.getContext('2d');

// Make canvas focusable for keyboard events
canvas.setAttribute('tabindex', '0');

// State
let isDrawing = false;
let isPanning = false;
let lastX = 0;
let lastY = 0;
let offsetX = 0;
let offsetY = 0;

// Mouse events
canvas.addEventListener('mousedown', (e) => {
  canvas.focus(); // Give focus for keyboard events

  if (e.button === 0) { // Left button
    isDrawing = true;
    lastX = e.offsetX;
    lastY = e.offsetY;
  } else if (e.button === 1) { // Middle button
    e.preventDefault(); // Prevent auto-scroll
    isPanning = true;
    lastX = e.offsetX;
    lastY = e.offsetY;
  }
});

canvas.addEventListener('mousemove', (e) => {
  if (isDrawing) {
    drawLine(lastX, lastY, e.offsetX, e.offsetY);
    lastX = e.offsetX;
    lastY = e.offsetY;
  } else if (isPanning) {
    const dx = e.offsetX - lastX;
    const dy = e.offsetY - lastY;
    pan(dx, dy);
    lastX = e.offsetX;
    lastY = e.offsetY;
  }
});

canvas.addEventListener('mouseup', (e) => {
  if (e.button === 0) isDrawing = false;
  if (e.button === 1) isPanning = false;
});

// Catch mouseup outside canvas
window.addEventListener('mouseup', () => {
  isDrawing = false;
  isPanning = false;
});

// Prevent context menu
canvas.addEventListener('contextmenu', (e) => {
  e.preventDefault();
});

// Keyboard events
canvas.addEventListener('keydown', (e) => {
  // Prevent default for arrow keys and space
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.key)) {
    e.preventDefault();
  }

  // Game-style movement (using physical keys)
  if (e.code === 'KeyW') moveUp();
  if (e.code === 'KeyS') moveDown();
  if (e.code === 'KeyA') moveLeft();
  if (e.code === 'KeyD') moveRight();

  // Shortcuts (using key values)
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault();
    save();
  }

  if (e.key === 'Escape') {
    cancel();
  }

  // Modifier example
  if (e.shiftKey && e.key === 'ArrowUp') {
    selectUpward();
  }
});

// Helper functions
function drawLine(x1, y1, x2, y2) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function pan(dx, dy) {
  offsetX += dx;
  offsetY += dy;
  render();
}

function moveUp() { /* ... */ }
function moveDown() { /* ... */ }
function moveLeft() { /* ... */ }
function moveRight() { /* ... */ }
function save() { /* ... */ }
function cancel() { /* ... */ }
function selectUpward() { /* ... */ }
function render() { /* ... */ }
```

---

## Browser Compatibility

All features documented here are **fully supported** in modern browsers as of 2026:
- Chrome/Edge (Chromium)
- Firefox
- Safari
- Opera

**Baseline:** Mouse events have been widely available since July 2015. Touch events and Pointer Events are fully supported in all modern browsers.

**Source:** [MDN - mousemove event](https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event)

---

## Summary of Best Practices

✅ **DO:**
- Use `offsetX`/`offsetY` for canvas-relative coordinates
- Add `tabindex="0"` to canvas for keyboard events
- Use `event.key` for text input and shortcuts
- Use `event.code` for game controls and physical key positions
- Call `preventDefault()` to stop default browser actions
- Listen for `mouseup` on window to catch releases outside canvas
- Give focus to canvas on mousedown/mouseenter
- Handle both mouse and touch events for mobile support
- Consider Pointer Events API for unified input handling

❌ **DON'T:**
- Use deprecated `keyCode`, `charCode`, or `which` properties
- Use positive tabindex values (breaks tab order)
- Prevent Tab key (accessibility issue)
- Forget to prevent context menu if using right-click
- Ignore performance implications of high-frequency mousemove events
- Call preventDefault() on touchstart if you want mouse events to also fire

---

## Sources

### Official Documentation (HIGH Confidence)
- [MDN - Element: mousemove event](https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event)
- [MDN - KeyboardEvent](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent)
- [MDN - KeyboardEvent: keyCode property](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/keyCode)
- [MDN - Touch events](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events)
- [MDN - Coordinate systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems)
- [MDN - Event: preventDefault() method](https://developer.mozilla.org/en-US/docs/Web/API/Event/preventDefault)
- [MDN - Event: stopPropagation() method](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation)
- [MDN - Element: contextmenu event](https://developer.mozilla.org/en-US/docs/Web/API/Element/contextmenu_event)

### Browser Vendor Documentation (HIGH Confidence)
- [Chrome - What's new with KeyboardEvents? Keys and codes!](https://developer.chrome.com/blog/keyboardevent-keys-codes)
- [Apple - Adding Mouse and Touch Controls to Canvas](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/HTML-canvas-guide/AddingMouseandTouchControlstoCanvas/AddingMouseandTouchControlstoCanvas.html)

### Web Standards and Accessibility (HIGH Confidence)
- [WebAIM: Keyboard Accessibility - Tabindex](https://webaim.org/techniques/keyboard/tabindex)
- [web.dev - Control focus with tabindex](https://web.dev/articles/control-focus-with-tabindex)

### Tutorials and Guides (MEDIUM Confidence)
- [Handling mouse input events for a HTML canvas game](https://stephendoddtech.com/blog/game-design/mouse-event-listener-input-html-canvas)
- [Working with the Mouse | KIRUPA](https://www.kirupa.com/canvas/working_with_the_mouse.htm)
- [The JavaScript Mouse Event Mystery: clientX, pageX, offsetX Explained](https://medium.com/@greenduckstudiogames/the-javascript-mouse-event-mystery-clientx-pagex-offsetx-explained-eccd8231fc81)
- [Keyboard: keydown and keyup](https://javascript.info/keyboard-events)
- [Should I use e.code or e.key when handling keyboard events?](https://blog.andri.co/022-should-i-use-ecode-or-ekey-when-handling-keyboard-events/)
- [Using Touch Events with the HTML5 Canvas](https://bencentra.com/code/2014/12/05/html5-canvas-touch-events.html)
- [Canvas key events](http://www.dbp-consulting.com/tutorials/canvas/CanvasKeyEvents.html)
- [How to detect different mouse button clicks](https://accreditly.io/articles/how-to-detect-different-mouse-button-clicks)
- [How to Disable Right Click on a Website Using JavaScript](https://coreui.io/blog/how-to-disable-right-click-on-a-website-using-javascript/)

### Framework Documentation (MEDIUM Confidence)
- [Konva - HTML5 Canvas Mobile Touch Events Tutorial](https://konvajs.org/docs/events/Mobile_Events.html)
- [Konva - HTML5 Canvas Keyboard events](https://konvajs.org/docs/events/Keyboard_Events.html)
- [PlayCanvas - Basic Mouse Input](https://developer.playcanvas.com/tutorials/mouse-input/)
