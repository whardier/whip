# Browser to Screen Coordinate Mapping Research

**Researched:** 2026-02-09
**Confidence:** HIGH

## Executive Summary

Mapping browser coordinates to screen coordinates involves navigating multiple coordinate systems (offset, client/viewport, page, screen, NDC), handling DPI scaling (especially on Retina displays), and choosing appropriate scaling strategies (stretch, letterbox, 1:1). The browser provides four distinct coordinate systems, each with different origin points and use cases. High-DPI displays require careful handling of `devicePixelRatio` to avoid blurry rendering, and multi-monitor setups require the Window Management API for accurate cross-screen positioning.

**Key Technical Challenges:**
1. Canvas has two dimension systems: display size (CSS) and buffer size (actual pixels)
2. Retina/HiDPI displays require 2x+ pixel buffers with coordinate system normalization
3. Multi-monitor setups use multi-screen origin (0,0 at OS primary screen) for absolute positioning
4. Aspect ratio preservation requires choosing min(scaleX, scaleY) and letterboxing/pillarboxing

---

## 1. Browser Coordinate Systems

Browsers use **four standard coordinate systems** with different origins and use cases.

### 1.1 System Definitions

| System | Origin | Use Case | Properties | When to Use |
|--------|--------|----------|------------|-------------|
| **Offset** | Top-left of element itself | Element-relative positioning | `offsetX`, `offsetY` | Drawing on canvas, element-specific interactions |
| **Client/Viewport** | Top-left of viewport | Viewport-relative UI | `clientX`, `clientY` | Most common for UI interactions |
| **Page** | Top-left of entire document | Document-wide positioning | `pageX`, `pageY` | Scrollable content positioning |
| **Screen** | Top-left of user's screen | Absolute screen position | `screenX`, `screenY` | System-level positioning, multi-monitor |

**Source:** [MDN Coordinate Systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems)

### 1.2 Coordinate Direction Convention

- **X-axis:** Negative = left, Positive = right
- **Y-axis:** Negative = above, Positive = below (unlike traditional math!)
- **Z-axis:** Depth/layering (CSS `z-index`)

**Important:** Web coordinates use top-left origin with positive Y pointing downward.

### 1.3 Transformations Between Systems

```
Client → Page:    Add scroll offset (scrollX, scrollY)
Client → Screen:  Add window position (screenLeft, screenTop)
Offset → Client:  Add element's viewport position (from getBoundingClientRect)
Page → Offset:    Subtract element's page position
```

### 1.4 Practical Mouse Event Example

```javascript
canvas.addEventListener('mousemove', (e) => {
  console.log(`
    Offset:   ${e.offsetX}, ${e.offsetY}     // Relative to canvas
    Client:   ${e.clientX}, ${e.clientY}     // Relative to viewport
    Page:     ${e.pageX}, ${e.pageY}         // Relative to document
    Screen:   ${e.screenX}, ${e.screenY}     // Relative to screen
  `);
});
```

**Sources:**
- [MDN Coordinate Systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems)
- [Translating Viewport Coordinates](https://www.bennadel.com/blog/3441-translating-viewport-coordinates-into-element-local-coordinates-using-element-getboundingclientrect.htm)

---

## 2. Canvas Coordinate Transformation

### 2.1 Canvas Two-Size System

Canvas elements have **two separate dimension systems:**

1. **Display size** — CSS pixels (how it appears visually)
2. **Drawing buffer size** — Actual pixel resolution (what gets rendered)

```html
<!-- 111x222 pixel buffer displayed at 333x444 CSS pixels -->
<canvas width="111" height="222" style="width: 333px; height: 444px;"></canvas>
```

**Why separate?** Allows high-DPI rendering without changing coordinate system.

### 2.2 Mouse to Canvas Coordinates

**Basic transformation using getBoundingClientRect:**

```javascript
const canvas = document.getElementById('myCanvas');
const rect = canvas.getBoundingClientRect();

canvas.addEventListener('click', (e) => {
  // Method 1: Direct offsetX/offsetY (simplest)
  const canvasX1 = e.offsetX;
  const canvasY1 = e.offsetY;

  // Method 2: Manual calculation (more control)
  const canvasX2 = e.clientX - rect.left;
  const canvasY2 = e.clientY - rect.top;

  // Method 3: Account for canvas scaling (buffer != display)
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const bufferX = (e.clientX - rect.left) * scaleX;
  const bufferY = (e.clientY - rect.top) * scaleY;
});
```

**Key insight:** When canvas display size differs from buffer size, mouse coordinates need scaling.

**Sources:**
- [HTML5 Canvas Mouse Coordinates](https://www.html5canvastutorials.com/advanced/html5-canvas-mouse-coordinates/)
- [getBoundingClientRect Positioning](https://jwood206.medium.com/positioning-with-mouse-events-offset-getboundingclientrect-and-getcomputedstyle-afe12bfcb5f)

### 2.3 Handling Canvas Transforms

For canvases with applied transformations (rotate, scale, translate):

```javascript
const ctx = canvas.getContext('2d');
const transform = ctx.getTransform(); // Returns DOMMatrix

// Transform properties:
// e = horizontal translation
// f = vertical translation
// a = horizontal scaling
// d = vertical scaling

const adjustedX = mouseX - transform.e;
const adjustedY = mouseY - transform.f;
```

**Source:** [Transforming Mouse Coordinates](https://roblouie.com/article/617/transforming-mouse-coordinates-to-canvas-coordinates/)

---

## 3. Screen Resolution Detection on macOS

### 3.1 Basic Detection APIs

```javascript
// CSS pixels (logical)
const screenWidth = window.screen.width;
const screenHeight = window.screen.height;

// Available area (excluding OS UI)
const availWidth = window.screen.availWidth;
const availHeight = window.screen.availHeight;

// Viewport size
const viewportWidth = window.innerWidth;
const viewportHeight = window.innerHeight;
```

### 3.2 Physical Resolution on Retina Displays

macOS Retina displays use **device pixel ratio** (typically 2.0) to map CSS pixels to physical pixels:

```javascript
// Retina detection
const dpr = window.devicePixelRatio; // 1.0 = standard, 2.0+ = Retina/HiDPI

// Physical resolution
const physicalWidth = window.screen.width * dpr;
const physicalHeight = window.screen.height * dpr;

// Example: MacBook Pro 13" Retina
// CSS: 1440 x 900
// Physical: 2880 x 1800
// DPR: 2.0
```

**Important:** `window.screen` returns CSS pixels, not physical pixels. Always multiply by `devicePixelRatio` for actual hardware resolution.

**Sources:**
- [MDN devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio)
- [Screen Resolution Detection](https://www.tutorialrepublic.com/faq/how-to-detect-screen-resolution-with-javascript.php)

### 3.3 Detecting Resolution Changes

Monitor when user moves window between displays:

```javascript
function watchDevicePixelRatio() {
  const mqString = `(resolution: ${window.devicePixelRatio}dppx)`;
  const media = matchMedia(mqString);

  media.addEventListener('change', () => {
    console.log('DPR changed to:', window.devicePixelRatio);
    // Re-initialize canvas for new display
    watchDevicePixelRatio(); // Re-register with new value
  });
}

watchDevicePixelRatio();
```

**Source:** [MDN devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio)

---

## 4. DPI / Retina Scaling Issues

### 4.1 The Problem

On Retina displays, browsers must render more physical pixels than CSS pixels:
- Standard display: 1 CSS pixel = 1 physical pixel
- Retina display: 1 CSS pixel = 2x2 (or more) physical pixels

**Without correction:** Canvas content appears blurry because browser upscales the low-res buffer.

### 4.2 The Solution: Dual-Size Canvas

Three-step approach:

1. **Scale the buffer** by `devicePixelRatio`
2. **Normalize the coordinate system** with `ctx.scale()`
3. **Set display size** with CSS

```javascript
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Desired display size in CSS pixels
const displayWidth = 800;
const displayHeight = 600;

// 1. Set CSS display size
canvas.style.width = `${displayWidth}px`;
canvas.style.height = `${displayHeight}px`;

// 2. Scale buffer by device pixel ratio
const dpr = window.devicePixelRatio || 1;
canvas.width = displayWidth * dpr;
canvas.height = displayHeight * dpr;

// 3. Normalize coordinate system (CRITICAL!)
ctx.scale(dpr, dpr);

// Now draw normally using CSS pixel coordinates
ctx.fillRect(10, 10, 100, 100); // Works in CSS pixels!
```

**Why `ctx.scale()` matters:** It transforms the coordinate system so you can use CSS pixel coordinates while the canvas renders at physical pixel resolution.

**Sources:**
- [WebGL HandlingHighDPI](https://wikis.khronos.org/webgl/HandlingHighDPI)
- [Canvas Retina Fix](https://gist.github.com/callumlocke/cc258a193839691f60dd)
- [Ensuring Canvas Looks Good on Retina](https://www.kirupa.com/canvas/canvas_high_dpi_retina.htm)

### 4.3 Modern Approach: ResizeObserver

Automatically handle canvas resizing and DPI changes:

```javascript
const observer = new ResizeObserver((entries) => {
  const entry = entries[0];
  let width, height;

  if (entry.devicePixelContentBoxSize) {
    // Modern approach: direct device pixel dimensions
    width = entry.devicePixelContentBoxSize[0].inlineSize;
    height = entry.devicePixelContentBoxSize[0].blockSize;
  } else {
    // Fallback for Safari
    const dpr = window.devicePixelRatio;
    width = Math.round(entry.contentBoxSize[0].inlineSize * dpr);
    height = Math.round(entry.contentBoxSize[0].blockSize * dpr);
  }

  canvas.width = width;
  canvas.height = height;
});

observer.observe(canvas);
```

**Source:** [WebGL HandlingHighDPI](https://wikis.khronos.org/webgl/HandlingHighDPI)

### 4.4 Input Coordinate Transformation on Retina

Mouse events deliver CSS pixel coordinates, requiring conversion to match the scaled buffer:

```javascript
canvas.addEventListener('mousemove', (e) => {
  // WRONG: Don't apply DPR to position
  // const x = e.offsetX * devicePixelRatio; // NO!

  // CORRECT: Scale by canvas dimension ratio
  const scaleX = canvas.width / canvas.offsetWidth;
  const scaleY = canvas.height / canvas.offsetHeight;
  const canvasX = e.offsetX * scaleX;
  const canvasY = e.offsetY * scaleY;
});
```

**Critical:** Canvas position remains in CSS pixels. Only the buffer dimensions change.

**Source:** [WebGL HandlingHighDPI](https://wikis.khronos.org/webgl/HandlingHighDPI)

---

## 5. Scaling Strategies

Three primary approaches for fitting content to different screen sizes while handling aspect ratios.

### 5.1 Strategy Comparison

| Strategy | Aspect Ratio | Black Bars | Content Coverage | Use Case |
|----------|--------------|------------|------------------|----------|
| **Stretch** | Not preserved | No | 100% | When distortion acceptable |
| **Letterbox/Pillarbox** | Preserved | Yes | Partial | Preserve original appearance |
| **1:1 (No scaling)** | N/A | Depends | Depends | Pixel-perfect rendering |

### 5.2 Letterbox Scaling (Aspect Ratio Preserved)

**Definition:** Scale content to fit screen while maintaining aspect ratio. Add black bars (mattes) to fill remaining space.

- **Letterbox:** Horizontal bars (top/bottom) when content wider than screen
- **Pillarbox:** Vertical bars (left/right) when content narrower than screen

**Formula:**

```javascript
function getLetterboxScale(contentWidth, contentHeight, screenWidth, screenHeight) {
  const scaleX = screenWidth / contentWidth;
  const scaleY = screenHeight / contentHeight;

  // Use MINIMUM to ensure content fits entirely
  return Math.min(scaleX, scaleY);
}

// Apply scale
const scale = getLetterboxScale(1920, 1080, window.innerWidth, window.innerHeight);
const scaledWidth = 1920 * scale;
const scaledHeight = 1080 * scale;

// Center with black bars
const offsetX = (window.innerWidth - scaledWidth) / 2;
const offsetY = (window.innerHeight - scaledHeight) / 2;
```

**CSS Transform Approach:**

```javascript
function letterboxCanvas(canvas) {
  const scaleX = (window.innerWidth - 10) / canvas.width;
  const scaleY = (window.innerHeight - 10) / canvas.height;
  const scale = Math.min(scaleX, scaleY);

  canvas.style.transform = `scale(${scale})`;
  canvas.style.transformOrigin = 'center top';
}

window.addEventListener('resize', () => letterboxCanvas(canvas));
```

**Sources:**
- [Stretch Canvas to Fill Window](https://gist.github.com/zachstronaut/1184900)
- [Wikipedia: Letterboxing](https://en.wikipedia.org/wiki/Letterboxing_(filming))
- [Letterboxing vs Pillarboxing](https://www.linkedin.com/advice/3/what-pros-cons-using-letterboxing-pillarboxing-your)

### 5.3 Stretch Scaling (No Aspect Ratio)

**Definition:** Scale content independently on each axis to fill entire screen.

```javascript
canvas.style.width = '100%';
canvas.style.height = '100%';

// Or with explicit dimensions:
canvas.style.width = `${window.innerWidth}px`;
canvas.style.height = `${window.innerHeight}px`;
```

**Drawback:** Distorts content if aspect ratios don't match.

### 5.4 1:1 Pixel Mapping (No Scaling)

**Definition:** One canvas pixel = one screen pixel. No scaling applied.

```javascript
canvas.width = window.innerWidth * devicePixelRatio;
canvas.height = window.innerHeight * devicePixelRatio;
canvas.style.width = `${window.innerWidth}px`;
canvas.style.height = `${window.innerHeight}px`;
```

**Use case:** Pixel-perfect rendering, technical applications, image editing.

### 5.5 CSS object-fit for Automatic Letterboxing

Modern CSS property for automatic aspect ratio handling:

```css
canvas {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Letterbox */
  /* object-fit: cover;  Fill, crop edges */
  /* object-fit: fill;   Stretch */
}
```

**Sources:**
- [WebGL Resizing Canvas](https://webglfundamentals.org/webgl/lessons/webgl-resizing-the-canvas.html)
- [Canvas Scaling Strategies](https://joshondesign.com/2023/04/15/canvas_scale_smooth)

---

## 6. Multi-Monitor Handling

### 6.1 Multi-Screen Origin

The **multi-screen origin** is the (0,0) point in the OS's virtual screen arrangement:

- **Location:** Top-left corner of OS primary screen (by convention)
- **Coordinate direction:**
  - Positive: right and downward
  - Negative: left and upward

**Example configuration:**

```
Primary (1920x1080):      left/top = (0, 0)
Secondary right (1440x900): left/top = (1920, 0)
Secondary left (1440x900):  left/top = (-1440, 0)
```

**Source:** [MDN Multi-screen Origin](https://developer.mozilla.org/en-US/docs/Web/API/Window_Management_API/Multi-screen_origin)

### 6.2 Window Management API

**Modern approach** for multi-monitor applications (Chrome 100+, Edge 100+):

```javascript
// Request permission
const permission = await navigator.permissions.query({
  name: 'window-management'
});

if (permission.state === 'granted') {
  // Get all screens
  const screenDetails = await window.getScreenDetails();

  screenDetails.screens.forEach(screen => {
    console.log(`
      Screen: ${screen.label}
      Position: ${screen.left}, ${screen.top}
      Size: ${screen.width} x ${screen.height}
      Available: ${screen.availLeft}, ${screen.availTop}
      Available Size: ${screen.availWidth} x ${screen.availHeight}
      Primary: ${screen.isPrimary}
      DPR: ${screen.devicePixelRatio}
    `);
  });

  // Open window on specific screen
  const secondaryScreen = screenDetails.screens[1];
  window.open(
    'content.html',
    '_blank',
    `left=${secondaryScreen.availLeft},
     top=${secondaryScreen.availTop},
     width=${secondaryScreen.availWidth},
     height=${secondaryScreen.availHeight}`
  );
}
```

**Sources:**
- [MDN getScreenDetails](https://developer.mozilla.org/en-US/docs/Web/API/Window/getScreenDetails)
- [Chrome Window Management API](https://developer.chrome.com/docs/capabilities/web-apis/window-management)
- [W3C Window Management Explainer](https://github.com/w3c/window-management/blob/main/EXPLAINER.md)

### 6.3 Legacy Multi-Monitor Detection

**Without Window Management API:**

```javascript
// Screen where current window is located
const currentScreen = {
  left: window.screenLeft || window.screenX,
  top: window.screenTop || window.screenY,
  width: window.screen.width,
  height: window.screen.height
};

// Detect if window spans multiple monitors (approximate)
const windowRight = currentScreen.left + window.innerWidth;
const windowBottom = currentScreen.top + window.innerHeight;
const spansScreens = (
  windowRight > currentScreen.width ||
  windowBottom > currentScreen.height
);
```

**Limitation:** Cannot enumerate all screens without Window Management API.

### 6.4 Considerations for Coordinate Mapping

1. **Different DPR per monitor:** Each screen may have different `devicePixelRatio`
2. **Virtual arrangement:** Screens form a 2D grid with potential gaps
3. **Permission required:** User must grant "window-management" permission
4. **Browser support:** Limited to Chromium-based browsers (as of 2026)

**Source:** [Multi-Screen Window Placement](https://webscreens.github.io/window-placement/)

---

## 7. Coordinate Normalization

### 7.1 Why Normalize?

**Benefits:**
- Resolution-independent
- Better numerical stability for algorithms
- Consistent across different displays
- Easier mathematical operations

**Common ranges:**
- **[0, 1]:** Natural for percentages and interpolation
- **[-1, 1]:** Used in graphics (NDC - Normalized Device Coordinates)

### 7.2 Pixel to [0, 1] Normalization

```javascript
// Normalize pixel coordinates to 0-1 range
function normalizeCoordinates(x, y, width, height) {
  return {
    x: x / width,
    y: y / height
  };
}

// Denormalize back to pixels
function denormalizeCoordinates(normX, normY, width, height) {
  return {
    x: normX * width,
    y: normY * height
  };
}

// Example: Mouse click to normalized
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const pixelX = e.clientX - rect.left;
  const pixelY = e.clientY - rect.top;

  const normalized = normalizeCoordinates(
    pixelX, pixelY,
    rect.width, rect.height
  );

  console.log(`Normalized: ${normalized.x}, ${normalized.y}`);
  // Range: 0.0 to 1.0 for both axes
});
```

### 7.3 Pixel to [-1, 1] NDC (Graphics Standard)

```javascript
// Used in WebGL/OpenGL
function pixelToNDC(x, y, width, height) {
  return {
    x: (x / width) * 2 - 1,    // 0→width maps to -1→1
    y: -((y / height) * 2 - 1) // 0→height maps to 1→-1 (flip Y)
  };
}

// NDC back to pixels
function ndcToPixel(ndcX, ndcY, width, height) {
  return {
    x: (ndcX + 1) * 0.5 * width,
    y: (1 - ndcY) * 0.5 * height // Flip Y
  };
}
```

**Y-axis flip:** Graphics APIs typically use bottom-left origin, while DOM uses top-left.

**Sources:**
- [LearnOpenGL Coordinate Systems](https://learnopengl.com/Getting-started/Coordinate-Systems)
- [Normalized Device Coordinates](https://apoorvaj.io/ndc-clip)

### 7.4 Browser to Screen Normalization (Cross-Resolution)

Map browser coordinates to normalized screen space:

```javascript
async function browserToNormalizedScreen(clientX, clientY) {
  const screenDetails = await window.getScreenDetails();
  const currentScreen = screenDetails.currentScreen;

  // Convert client to screen coordinates
  const screenX = clientX + window.screenLeft;
  const screenY = clientY + window.screenTop;

  // Normalize to current screen
  const normalized = {
    x: (screenX - currentScreen.left) / currentScreen.width,
    y: (screenY - currentScreen.top) / currentScreen.height
  };

  return normalized; // 0-1 range relative to current screen
}

// Map normalized coordinates to different screen
async function normalizedToTargetScreen(normX, normY, targetScreenIndex) {
  const screenDetails = await window.getScreenDetails();
  const targetScreen = screenDetails.screens[targetScreenIndex];

  return {
    x: targetScreen.left + (normX * targetScreen.width),
    y: targetScreen.top + (normY * targetScreen.height)
  };
}
```

**Use case:** Coordinate persistence across sessions, resolution changes, or multi-monitor setups.

---

## 8. Maintaining Aspect Ratio During Mapping

### 8.1 The Aspect Ratio Problem

When mapping coordinates between spaces with different aspect ratios, you must decide:

1. **Preserve aspect ratio?** (letterbox/pillarbox)
2. **Stretch to fill?** (distortion)
3. **Crop content?** (data loss)

### 8.2 Aspect-Preserving Coordinate Transform

```javascript
function createAspectPreservingTransform(
  sourceWidth, sourceHeight,
  targetWidth, targetHeight
) {
  // Calculate scales
  const scaleX = targetWidth / sourceWidth;
  const scaleY = targetHeight / sourceHeight;

  // Use minimum to preserve aspect ratio
  const scale = Math.min(scaleX, scaleY);

  // Calculate letterbox/pillarbox offsets
  const scaledWidth = sourceWidth * scale;
  const scaledHeight = sourceHeight * scale;
  const offsetX = (targetWidth - scaledWidth) / 2;
  const offsetY = (targetHeight - scaledHeight) / 2;

  return {
    scale,
    offsetX,
    offsetY,
    scaledWidth,
    scaledHeight,

    // Transform function: source → target
    transform: (x, y) => ({
      x: x * scale + offsetX,
      y: y * scale + offsetY
    }),

    // Inverse transform: target → source
    inverse: (x, y) => ({
      x: (x - offsetX) / scale,
      y: (y - offsetY) / scale
    })
  };
}

// Example: Map from 1920x1080 content to 1440x900 display
const transform = createAspectPreservingTransform(1920, 1080, 1440, 900);

// Transform content coordinate to display
const displayCoords = transform.transform(960, 540); // Center of content

// Transform display click to content coordinate
const contentCoords = transform.inverse(720, 450); // Center of display
```

### 8.3 Handling Click Events in Letterboxed Canvas

```javascript
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();

  // Get click position in display space
  const displayX = e.clientX - rect.left;
  const displayY = e.clientY - rect.top;

  // Transform to content space (accounting for letterbox)
  const contentCoords = transform.inverse(displayX, displayY);

  // Check if click is within content area (not in black bars)
  const inBounds = (
    contentCoords.x >= 0 && contentCoords.x <= 1920 &&
    contentCoords.y >= 0 && contentCoords.y <= 1080
  );

  if (inBounds) {
    console.log('Content click:', contentCoords);
  } else {
    console.log('Click in letterbox area');
  }
});
```

**Source:** [Canvas Automatic Scaling](https://www.ckollars.org/canvas-two-coordinate-scales.html)

### 8.4 CSS-Based Aspect Ratio Maintenance

Modern approach using CSS:

```css
.canvas-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: black; /* Letterbox color */
}

canvas {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  aspect-ratio: 16 / 9; /* Or calculate from canvas.width/height */
}
```

**Source:** [How to Scale Canvas While Preserving Aspect Ratio](https://jslegenddev.substack.com/p/how-to-scale-the-canvas-while-preserving)

---

## 9. Affine Transformation Matrices

### 9.1 Overview

Affine transformations combine linear transformations (scale, rotate, shear) with translation. Represented as 3x3 matrices for 2D transformations.

**Matrix structure:**

```
| a  c  e |   | scaleX   shearX    translateX |
| b  d  f | = | shearY   scaleY    translateY |
| 0  0  1 |   | 0        0         1          |
```

### 9.2 Canvas Transform API

```javascript
const ctx = canvas.getContext('2d');

// Apply transformation matrix
ctx.transform(a, b, c, d, e, f);

// Common transformations:
ctx.scale(sx, sy);           // → transform(sx, 0, 0, sy, 0, 0)
ctx.rotate(angle);           // → transform(cos, sin, -sin, cos, 0, 0)
ctx.translate(tx, ty);       // → transform(1, 0, 0, 1, tx, ty)

// Get current transformation
const matrix = ctx.getTransform(); // Returns DOMMatrix

// Reset to identity
ctx.setTransform(1, 0, 0, 1, 0, 0);
```

**Sources:**
- [MDN transform()](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/transform)
- [HTML5 Canvas Matrix Transforms](https://www.w3resource.com/html5-canvas/html5-canvas-matrix-transforms.php)

### 9.3 Coordinate Transformation with Matrices

```javascript
function transformPoint(x, y, matrix) {
  return {
    x: x * matrix.a + y * matrix.c + matrix.e,
    y: x * matrix.b + y * matrix.d + matrix.f
  };
}

// Example: Transform mouse to canvas space
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const displayX = e.clientX - rect.left;
  const displayY = e.clientY - rect.top;

  // Get inverse transformation (canvas → world)
  const ctx = canvas.getContext('2d');
  const matrix = ctx.getTransform().inverse();

  const worldCoords = transformPoint(displayX, displayY, matrix);
  console.log('World coordinates:', worldCoords);
});
```

### 9.4 Common Transformation Patterns

**Centering and scaling:**

```javascript
// Center origin and scale
function setupCanvasTransform(canvas, scale) {
  const ctx = canvas.getContext('2d');

  // Move origin to center
  ctx.translate(canvas.width / 2, canvas.height / 2);

  // Flip Y-axis for traditional math coordinates
  ctx.scale(scale, -scale);
}
```

**Viewport transform (world → screen):**

```javascript
function worldToScreen(worldX, worldY, camera) {
  // 1. Translate by camera position
  let x = worldX - camera.x;
  let y = worldY - camera.y;

  // 2. Apply camera zoom
  x *= camera.zoom;
  y *= camera.zoom;

  // 3. Translate to screen center
  x += canvas.width / 2;
  y += canvas.height / 2;

  return { x, y };
}
```

**Sources:**
- [Transformation Matrix JS](https://github.com/epistemex/transformation-matrix-js)
- [Transformations in HTML5 Canvas](https://zetcode.com/gfx/html5canvas/transformations/)

---

## 10. Common Patterns and Best Practices

### 10.1 Complete Retina-Ready Canvas Setup

```javascript
class RetinaCanvas {
  constructor(canvasId, logicalWidth, logicalHeight) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.logicalWidth = logicalWidth;
    this.logicalHeight = logicalHeight;

    this.setupCanvas();
    this.watchForChanges();
  }

  setupCanvas() {
    const dpr = window.devicePixelRatio || 1;

    // Set display size
    this.canvas.style.width = `${this.logicalWidth}px`;
    this.canvas.style.height = `${this.logicalHeight}px`;

    // Set buffer size
    this.canvas.width = this.logicalWidth * dpr;
    this.canvas.height = this.logicalHeight * dpr;

    // Normalize coordinate system
    this.ctx.scale(dpr, dpr);
  }

  watchForChanges() {
    // Detect DPI changes (moving between monitors)
    const mqString = `(resolution: ${window.devicePixelRatio}dppx)`;
    const media = matchMedia(mqString);
    media.addEventListener('change', () => {
      this.setupCanvas();
      this.watchForChanges(); // Re-register
    });
  }

  getCanvasCoordinates(e) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  }
}

// Usage
const canvas = new RetinaCanvas('myCanvas', 800, 600);
```

### 10.2 Multi-Screen Coordinate Mapping Pattern

```javascript
class ScreenMapper {
  constructor() {
    this.initialized = false;
    this.screens = [];
  }

  async initialize() {
    const permission = await navigator.permissions.query({
      name: 'window-management'
    });

    if (permission.state !== 'granted') {
      throw new Error('Window management permission denied');
    }

    const screenDetails = await window.getScreenDetails();
    this.screens = screenDetails.screens;
    this.initialized = true;
  }

  // Convert browser coordinates to normalized multi-screen space
  browserToNormalized(clientX, clientY) {
    const screenX = clientX + window.screenLeft;
    const screenY = clientY + window.screenTop;

    // Find total bounds of all screens
    const bounds = this.getTotalBounds();

    return {
      x: (screenX - bounds.left) / bounds.width,
      y: (screenY - bounds.top) / bounds.height
    };
  }

  // Convert normalized coordinates to specific screen pixels
  normalizedToScreen(normX, normY, screenIndex) {
    const screen = this.screens[screenIndex];
    return {
      x: screen.left + (normX * screen.width),
      y: screen.top + (normY * screen.height)
    };
  }

  getTotalBounds() {
    const left = Math.min(...this.screens.map(s => s.left));
    const top = Math.min(...this.screens.map(s => s.top));
    const right = Math.max(...this.screens.map(s => s.left + s.width));
    const bottom = Math.max(...this.screens.map(s => s.top + s.height));

    return {
      left,
      top,
      width: right - left,
      height: bottom - top
    };
  }
}
```

### 10.3 Aspect-Preserving Full-Screen Pattern

```javascript
class FullscreenCanvas {
  constructor(canvas, contentWidth, contentHeight) {
    this.canvas = canvas;
    this.contentWidth = contentWidth;
    this.contentHeight = contentHeight;

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    const scaleX = window.innerWidth / this.contentWidth;
    const scaleY = window.innerHeight / this.contentHeight;
    const scale = Math.min(scaleX, scaleY);

    // Calculate letterbox dimensions
    this.displayWidth = this.contentWidth * scale;
    this.displayHeight = this.contentHeight * scale;
    this.offsetX = (window.innerWidth - this.displayWidth) / 2;
    this.offsetY = (window.innerHeight - this.displayHeight) / 2;

    // Apply to canvas
    this.canvas.style.width = `${this.displayWidth}px`;
    this.canvas.style.height = `${this.displayHeight}px`;
    this.canvas.style.position = 'absolute';
    this.canvas.style.left = `${this.offsetX}px`;
    this.canvas.style.top = `${this.offsetY}px`;
  }

  screenToContent(screenX, screenY) {
    // Remove letterbox offset
    const displayX = screenX - this.offsetX;
    const displayY = screenY - this.offsetY;

    // Scale to content coordinates
    const scale = this.displayWidth / this.contentWidth;
    const contentX = displayX / scale;
    const contentY = displayY / scale;

    // Check bounds
    const inBounds = (
      contentX >= 0 && contentX <= this.contentWidth &&
      contentY >= 0 && contentY <= this.contentHeight
    );

    return { x: contentX, y: contentY, inBounds };
  }
}

// Usage
const fsCanvas = new FullscreenCanvas(canvas, 1920, 1080);

canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const coords = fsCanvas.screenToContent(
    e.clientX - rect.left,
    e.clientY - rect.top
  );

  if (coords.inBounds) {
    console.log('Content click:', coords.x, coords.y);
  }
});
```

### 10.4 Coordinate System Cheat Sheet

```javascript
// Quick reference for common transformations

// 1. Mouse event → Canvas offset coordinates
const canvasX = e.offsetX;
const canvasY = e.offsetY;

// 2. Mouse event → Canvas coordinates (with getBoundingClientRect)
const rect = canvas.getBoundingClientRect();
const canvasX = e.clientX - rect.left;
const canvasY = e.clientY - rect.top;

// 3. Canvas → Buffer coordinates (accounting for DPI)
const bufferX = canvasX * (canvas.width / canvas.offsetWidth);
const bufferY = canvasY * (canvas.height / canvas.offsetHeight);

// 4. Client → Screen coordinates
const screenX = e.clientX + window.screenLeft;
const screenY = e.clientY + window.screenTop;

// 5. Client → Page coordinates (accounting for scroll)
const pageX = e.clientX + window.scrollX;
const pageY = e.clientY + window.scrollY;

// 6. Pixel → Normalized [0,1]
const normX = x / width;
const normY = y / height;

// 7. Pixel → NDC [-1,1]
const ndcX = (x / width) * 2 - 1;
const ndcY = -((y / height) * 2 - 1); // Flip Y

// 8. Screen → Physical pixels (Retina)
const physicalX = screenX * window.devicePixelRatio;
const physicalY = screenY * window.devicePixelRatio;
```

---

## 11. Browser API Support Matrix

| Feature | Chrome | Firefox | Safari | Edge | Notes |
|---------|--------|---------|--------|------|-------|
| `devicePixelRatio` | ✅ | ✅ | ✅ | ✅ | Universal support |
| `ResizeObserver` | ✅ 64+ | ✅ 69+ | ✅ 13.1+ | ✅ 79+ | Modern standard |
| `devicePixelContentBoxSize` | ✅ 84+ | ❌ | ❌ | ✅ 84+ | Fallback needed |
| `getBoundingClientRect()` | ✅ | ✅ | ✅ | ✅ | Universal support |
| `Window Management API` | ✅ 100+ | ❌ | ❌ | ✅ 100+ | Chromium only |
| `getScreenDetails()` | ✅ 100+ | ❌ | ❌ | ✅ 100+ | Requires permission |
| `matchMedia` for DPR | ✅ | ✅ | ✅ | ✅ | Monitor resolution changes |
| `object-fit` CSS | ✅ | ✅ | ✅ | ✅ | Modern browsers |

**Key Takeaway:** Window Management API is Chromium-exclusive (as of 2026). For cross-browser multi-monitor support, use fallback detection.

---

## 12. Common Pitfalls and Solutions

### Pitfall 1: Forgetting ctx.scale() After DPI Adjustment

**Problem:**
```javascript
// WRONG: Canvas buffer sized for Retina, but coordinate system not scaled
canvas.width = 800 * devicePixelRatio;
canvas.height = 600 * devicePixelRatio;
ctx.fillRect(10, 10, 100, 100); // Draws tiny rectangle in corner!
```

**Solution:**
```javascript
// CORRECT: Scale coordinate system after resizing buffer
canvas.width = 800 * devicePixelRatio;
canvas.height = 600 * devicePixelRatio;
ctx.scale(devicePixelRatio, devicePixelRatio);
ctx.fillRect(10, 10, 100, 100); // Now draws at expected size
```

### Pitfall 2: Using offsetX/offsetY Without Scaling

**Problem:**
```javascript
// When canvas.width != canvas.offsetWidth
canvas.addEventListener('click', (e) => {
  ctx.fillRect(e.offsetX, e.offsetY, 5, 5); // Wrong position on Retina!
});
```

**Solution:**
```javascript
canvas.addEventListener('click', (e) => {
  const scaleX = canvas.width / canvas.offsetWidth;
  const scaleY = canvas.height / canvas.offsetHeight;
  const x = e.offsetX * scaleX;
  const y = e.offsetY * scaleY;
  ctx.fillRect(x, y, 5, 5); // Correct position
});
```

### Pitfall 3: Applying DPR to Mouse Position

**Problem:**
```javascript
// WRONG: Applying DPR to mouse coordinates
const x = e.offsetX * devicePixelRatio; // NO!
```

**Solution:**
```javascript
// CORRECT: DPR only affects canvas buffer size, not mouse position
// Mouse coordinates are already in CSS pixels
const x = e.offsetX;
```

### Pitfall 4: Not Handling DPR Changes

**Problem:** User moves window to external monitor with different DPI. Canvas becomes blurry.

**Solution:**
```javascript
// Monitor for DPR changes
function watchDPR() {
  const mqString = `(resolution: ${window.devicePixelRatio}dppx)`;
  matchMedia(mqString).addEventListener('change', () => {
    resizeCanvas(); // Re-initialize
    watchDPR(); // Re-register with new value
  });
}
```

### Pitfall 5: Ignoring Aspect Ratio in Letterbox Clicks

**Problem:** Treating clicks in black bars as valid content clicks.

**Solution:**
```javascript
function isClickInContent(x, y, transform) {
  const content = transform.inverse(x, y);
  return (
    content.x >= 0 && content.x <= contentWidth &&
    content.y >= 0 && content.y <= contentHeight
  );
}
```

---

## 13. Recommended Approach for Browser-to-Screen Mapping

Based on research findings, here's the recommended approach for a robust coordinate mapping system:

### Phase 1: Foundation (Browser → Canvas)

1. **Use ResizeObserver** for canvas sizing with DPI awareness
2. **Always call ctx.scale(dpr, dpr)** after resizing buffer
3. **Use getBoundingClientRect()** for mouse event transformations
4. **Monitor DPR changes** with matchMedia for multi-monitor support

### Phase 2: Scaling Strategy (Canvas → Display)

1. **Choose letterbox scaling** for aspect ratio preservation
2. **Calculate min(scaleX, scaleY)** to fit content
3. **Track offset values** for black bar regions
4. **Provide inverse transform** for click detection

### Phase 3: Screen Positioning (Multi-Monitor)

1. **Request Window Management API permission** (Chromium browsers)
2. **Use getScreenDetails()** to enumerate screens
3. **Store screen properties** (position, size, DPR)
4. **Implement fallback** for non-Chromium browsers using window.screen

### Phase 4: Normalization (Cross-Resolution Persistence)

1. **Normalize to [0, 1] range** for storage/transmission
2. **Denormalize based on target screen** dimensions
3. **Account for aspect ratio differences** when mapping
4. **Validate bounds** after transformation

### Complete Implementation Template

```javascript
class CoordinateMapper {
  constructor(canvas, contentWidth, contentHeight) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.contentWidth = contentWidth;
    this.contentHeight = contentHeight;

    this.setupCanvas();
    this.setupListeners();
  }

  setupCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();

    // 1. Retina handling
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);

    // 2. Letterbox calculation
    const scaleX = rect.width / this.contentWidth;
    const scaleY = rect.height / this.contentHeight;
    this.scale = Math.min(scaleX, scaleY);

    this.scaledWidth = this.contentWidth * this.scale;
    this.scaledHeight = this.contentHeight * this.scale;
    this.offsetX = (rect.width - this.scaledWidth) / 2;
    this.offsetY = (rect.height - this.scaledHeight) / 2;
  }

  setupListeners() {
    // Monitor DPI changes
    const mqString = `(resolution: ${window.devicePixelRatio}dppx)`;
    matchMedia(mqString).addEventListener('change', () => {
      this.setupCanvas();
      this.setupListeners();
    });

    // Monitor resize
    window.addEventListener('resize', () => this.setupCanvas());
  }

  // Browser (client) → Canvas coordinates
  clientToCanvas(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  }

  // Canvas → Content coordinates (accounting for letterbox)
  canvasToContent(canvasX, canvasY) {
    const contentX = (canvasX - this.offsetX) / this.scale;
    const contentY = (canvasY - this.offsetY) / this.scale;

    const inBounds = (
      contentX >= 0 && contentX <= this.contentWidth &&
      contentY >= 0 && contentY <= this.contentHeight
    );

    return { x: contentX, y: contentY, inBounds };
  }

  // Content → Normalized [0,1]
  contentToNormalized(contentX, contentY) {
    return {
      x: contentX / this.contentWidth,
      y: contentY / this.contentHeight
    };
  }

  // Normalized [0,1] → Content
  normalizedToContent(normX, normY) {
    return {
      x: normX * this.contentWidth,
      y: normY * this.contentHeight
    };
  }

  // Client → Screen (multi-monitor aware)
  clientToScreen(clientX, clientY) {
    return {
      x: clientX + window.screenLeft,
      y: clientY + window.screenTop
    };
  }

  // Complete transformation: Client → Normalized Content
  clientToNormalizedContent(clientX, clientY) {
    const canvas = this.clientToCanvas(clientX, clientY);
    const content = this.canvasToContent(canvas.x, canvas.y);

    if (!content.inBounds) {
      return { x: null, y: null, inBounds: false };
    }

    const normalized = this.contentToNormalized(content.x, content.y);
    return { ...normalized, inBounds: true };
  }
}

// Usage
const mapper = new CoordinateMapper(canvas, 1920, 1080);

canvas.addEventListener('click', (e) => {
  const normalized = mapper.clientToNormalizedContent(e.clientX, e.clientY);

  if (normalized.inBounds) {
    console.log(`Normalized click: ${normalized.x}, ${normalized.y}`);
    // Send to backend, store, or use for screen mapping
  }
});
```

---

## 14. Confidence Assessment

| Topic | Confidence | Reasoning |
|-------|------------|-----------|
| Browser coordinate systems | HIGH | Official MDN documentation, standardized APIs |
| Canvas DPI scaling | HIGH | Khronos WebGL wiki, extensive documentation |
| macOS screen detection | HIGH | Standard Web APIs, confirmed behavior |
| Multi-monitor API | MEDIUM | Limited to Chromium, evolving spec |
| Scaling strategies | HIGH | Mathematical fundamentals, established patterns |
| Normalization approaches | HIGH | Graphics programming standards (NDC) |
| Aspect ratio preservation | HIGH | Established letterbox/pillarbox techniques |
| Affine transformations | HIGH | Canvas 2D API specification |

**Overall Confidence: HIGH**

All core techniques are well-documented in official sources (MDN, Khronos, W3C). Multi-monitor support is the only area with lower confidence due to limited browser support, but fallback approaches are available.

---

## 15. Sources

### Official Documentation
- [MDN Coordinate Systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems)
- [MDN devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio)
- [MDN Multi-screen Origin](https://developer.mozilla.org/en-US/docs/Web/API/Window_Management_API/Multi-screen_origin)
- [MDN getScreenDetails](https://developer.mozilla.org/en-US/docs/Web/API/Window/getScreenDetails)
- [MDN transform()](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/transform)
- [Khronos WebGL HandlingHighDPI](https://wikis.khronos.org/webgl/HandlingHighDPI)

### Specifications
- [W3C Window Management Explainer](https://github.com/w3c/window-management/blob/main/EXPLAINER.md)
- [Multi-Screen Window Placement Spec](https://webscreens.github.io/window-placement/)
- [W3C CSSWG Viewport Issues](https://github.com/w3c/csswg-drafts/issues/5814)

### Technical Articles
- [Chrome Window Management API](https://developer.chrome.com/docs/capabilities/web-apis/window-management)
- [WebGL Resizing Canvas](https://webglfundamentals.org/webgl/lessons/webgl-resizing-the-canvas.html)
- [Ensuring Canvas Looks Good on Retina](https://www.kirupa.com/canvas/canvas_high_dpi_retina.htm)
- [Canvas Retina Fix Gist](https://gist.github.com/callumlocke/cc258a193839691f60dd)
- [Letterbox Canvas Gist](https://gist.github.com/zachstronaut/1184900)
- [LearnOpenGL Coordinate Systems](https://learnopengl.com/Getting-started/Coordinate-Systems)

### Community Resources
- [HTML5 Canvas Mouse Coordinates](https://www.html5canvastutorials.com/advanced/html5-canvas-mouse-coordinates/)
- [Translating Viewport Coordinates](https://www.bennadel.com/blog/3441-translating-viewport-coordinates-into-element-local-coordinates-using-element-getboundingclientrect.htm)
- [Canvas Scaling Strategies](https://joshondesign.com/2023/04/15/canvas_scale_smooth)
- [Canvas Automatic Scaling](https://www.ckollars.org/canvas-two-coordinate-scales.html)

### Graphics Standards
- [Normalized Device Coordinates](https://apoorvaj.io/ndc-clip)
- [Viewport Transform](https://www.mauriciopoppe.com/notes/computer-graphics/viewing/viewport-transform/)
- [Wikipedia: Letterboxing](https://en.wikipedia.org/wiki/Letterboxing_(filming))

---

## 16. Key Takeaways

1. **Four coordinate systems:** Offset, Client, Page, Screen — choose based on use case
2. **Canvas has two sizes:** Display (CSS) and buffer (pixels) — always normalize with ctx.scale()
3. **Retina requires 3 steps:** Scale buffer, normalize coordinates, transform mouse input
4. **Letterbox formula:** `Math.min(scaleX, scaleY)` preserves aspect ratio
5. **Multi-monitor needs permission:** Window Management API is Chromium-only, requires user grant
6. **Normalize for persistence:** [0,1] range makes coordinates resolution-independent
7. **Monitor DPR changes:** Use matchMedia to detect monitor switches
8. **ResizeObserver is modern:** Preferred over window.resize for canvas sizing
9. **Transform matrices stack:** Each ctx.transform() multiplies, use inverse for mouse input
10. **Validate bounds:** Always check if transformed coordinates fall within valid content area
