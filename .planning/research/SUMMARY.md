# Project Research Summary

**Project:** whip (Browser-to-Desktop Mouse Control System)
**Domain:** Real-time input capture, WebSocket communication, macOS automation
**Researched:** 2026-02-09
**Confidence:** HIGH

## Executive Summary

Whip is a real-time browser-to-desktop mouse control system that requires tight integration between three technical domains: browser input capture (canvas/DOM events), low-latency bidirectional communication (FastAPI WebSockets), and macOS input automation (pynput/PyAutoGUI). The research confirms this is a tractable MVP with well-documented components and proven patterns.

**Recommended approach:** Use HTML5 canvas with pointer events for browser input capture, FastAPI WebSockets with JSON protocol for bidirectional communication, and pynput for macOS mouse control. The critical path involves coordinate system normalization (browser coordinates to screen coordinates), sub-50ms latency optimization, and proper macOS Accessibility permission management. Multi-monitor support is achievable but adds complexity via coordinate mapping.

**Key risks:** Latency degradation from JSON protocol overhead, macOS Sequoia 15.0+ monthly permission renewals, coordinate mapping errors across different DPI displays, and WebSocket connection reliability under high-frequency mouse events. Mitigation strategies include binary protocol consideration for production, robust permission prompting UX, retina-aware coordinate transformation, and connection recovery patterns with heartbeat mechanisms.

## Key Findings

### Recommended Stack

**Browser-side (Input Capture):**
- **HTML5 Canvas** with pointer events for unified mouse/touch input capture
- Coordinate system: Use `offsetX/offsetY` for canvas-relative coordinates (simplest)
- `ResizeObserver` for automatic Retina/HiDPI handling with devicePixelRatio awareness
- Normalize coordinates to [0,1] range for resolution-independent transmission

**Backend (Communication Layer):**
- **FastAPI 0.115+** with native WebSocket support (Starlette-based)
- **JSON protocol** for MVP (human-readable debugging, rapid iteration)
- Binary protocol consideration for production (50+ msgs/sec threshold)
- **Connection management:** ConnectionManager pattern for tracking active clients
- **uvicorn** for development, **Gunicorn + Uvicorn workers** for production

**Desktop Automation (macOS):**
- **pynput 1.8.1+** as primary library (active maintenance, Python 3.12 compatible)
- Event monitoring capability, better multi-monitor support than PyAutoGUI
- **PyAutoGUI 0.9.54** as fallback for simpler API if monitoring not needed
- **Direct pyobjc/Quartz** for advanced control (if pynput insufficient)

**Core technologies:**
- **pynput:** macOS mouse control — actively maintained (March 2025), supports monitoring, Python 3.12 compatible
- **FastAPI:** WebSocket server — robust async/await, dependency injection, production-ready patterns
- **Canvas + ResizeObserver:** Browser input — standard APIs, automatic DPI handling, cross-browser support
- **Coordinate normalization:** Mapping layer — enables multi-resolution, multi-monitor persistence

### Expected Features

**Must have (table stakes):**
- **Capture mouse position** from browser canvas in real-time
- **Transmit coordinates** via WebSocket to backend server
- **Move macOS cursor** to absolute screen position
- **Coordinate transformation** from normalized browser coords to screen pixels
- **Connection status** indicator in browser UI
- **Basic error handling** for WebSocket disconnects and permission failures

**Should have (competitive):**
- **Multi-monitor support** via Window Management API (browser) + coordinate mapping
- **Retina display handling** with automatic devicePixelRatio detection
- **Sub-50ms latency** for responsive control (requires optimization)
- **Graceful degradation** when permissions denied or WebSocket fails
- **Visual feedback** showing active/inactive state in browser

**Defer (v2+):**
- **Keyboard input** forwarding (adds significant complexity)
- **Click/drag synthesis** (macOS drag requires duration parameter)
- **Multi-client broadcasting** (requires Redis Pub/Sub for scaling)
- **Binary protocol** (optimize after JSON MVP proves latency acceptable)
- **Touch input** support (unified pointer events handle this)
- **Authentication** (token-based or cookie-based WebSocket auth)

### Architecture Approach

The system consists of three logical layers with well-defined boundaries: **Browser Client** (input capture + coordinate normalization), **WebSocket Server** (FastAPI connection management + message routing), and **Desktop Controller** (coordinate denormalization + macOS automation). The browser captures canvas events, normalizes to [0,1] coordinates, and transmits via WebSocket. The server maintains connection state and forwards messages. The desktop controller denormalizes coordinates based on screen resolution/DPI and executes mouse movements via pynput.

**Major components:**

1. **Canvas Input Manager** (Browser)
   - Responsibilities: Capture pointer events, normalize coordinates, handle canvas scaling
   - Key patterns: ResizeObserver for DPI detection, offsetX/offsetY for coordinates, transform to [0,1]
   - Technologies: HTML5 Canvas, Pointer Events API, devicePixelRatio handling

2. **WebSocket Connection Manager** (FastAPI Server)
   - Responsibilities: Accept connections, route messages, handle disconnects, maintain active connection list
   - Key patterns: ConnectionManager singleton, async/await lifecycle, WebSocketDisconnect exception handling
   - Technologies: FastAPI WebSocket endpoints, JSON message protocol, dependency injection for auth

3. **Coordinate Mapper** (Shared Logic)
   - Responsibilities: Normalize browser coords, denormalize to screen coords, handle aspect ratio, DPI scaling
   - Key patterns: [0,1] normalization, letterbox/pillarbox transforms, multi-monitor offset calculation
   - Technologies: Math transformations, getBoundingClientRect (browser), screen detection APIs

4. **Desktop Automation Controller** (Python Backend)
   - Responsibilities: Move mouse to absolute screen position, handle multi-monitor, manage permissions
   - Key patterns: pynput Controller, coordinate validation, permission checking at startup
   - Technologies: pynput mouse.Controller, screen resolution detection, macOS Accessibility APIs

### Critical Pitfalls

**From macOS input control research:**

1. **Accessibility permissions required (CRITICAL)**
   - Problem: All Python input libraries silently fail without macOS Accessibility permission
   - Impact: Mouse control appears to work but does nothing, no error messages
   - Prevention: Check permissions programmatically on startup, display clear instructions, re-prompt on macOS Sequoia 15.0+ (monthly renewal)

2. **macOS Sequoia 15.0+ permission renewals**
   - Problem: Permissions expire monthly and after every reboot (new macOS behavior)
   - Impact: App stops working without warning, user confusion
   - Prevention: Implement permission monitoring, graceful degradation UX, clear re-prompt flow

3. **Multi-monitor coordinate complexity**
   - Problem: PyAutoGUI only works on primary monitor, secondary displays have offset coordinates
   - Impact: Mouse control fails or jumps to wrong position on multi-monitor setups
   - Prevention: Use pynput (better multi-monitor support), or implement coordinate offset calculation per screen

**From FastAPI WebSocket research:**

4. **Memory leaks from disconnected clients**
   - Problem: Failing to remove disconnected WebSocket clients from connection manager list
   - Impact: Memory grows unbounded, attempts to send to dead connections cause errors
   - Prevention: Always catch WebSocketDisconnect in try/except, remove from list in finally block, handle send failures

5. **High-frequency mousemove event flooding**
   - Problem: mousemove fires hundreds of times per second, overwhelming WebSocket/server
   - Impact: Latency degradation, dropped messages, server CPU saturation
   - Prevention: Throttle events client-side with requestAnimationFrame, implement server-side rate limiting, consider batching

**From canvas input research:**

6. **Canvas focus requirement for keyboard events**
   - Problem: Canvas elements don't receive keyboard events by default (if keyboard added later)
   - Impact: Keyboard shortcuts/controls silently fail
   - Prevention: Add tabindex="0" to canvas, focus on mousedown, provide visual focus indicator

**From coordinate mapping research:**

7. **Retina display coordinate scaling errors**
   - Problem: Canvas has two sizes (CSS display vs pixel buffer), mouse coordinates in CSS pixels
   - Impact: Clicks register at wrong positions, off by 2x on Retina displays
   - Prevention: Always call ctx.scale(dpr, dpr) after setting canvas.width/height, transform mouse coords by buffer/display ratio

8. **Aspect ratio distortion in letterbox mode**
   - Problem: Treating clicks in black bars as valid content, wrong coordinate mapping when aspect ratios differ
   - Impact: Mouse jumps to incorrect positions, clicks in dead zones
   - Prevention: Use Math.min(scaleX, scaleY) for letterbox, validate bounds after inverse transform, reject clicks outside content area

## Implications for Roadmap

Based on research, suggested phase structure prioritizes establishing the core data flow (browser → WebSocket → desktop) before optimizing for production concerns (latency, multi-monitor, reliability).

### Phase 1: Local Proof-of-Concept
**Rationale:** Validate the core technical integration (canvas input → WebSocket → pynput) works before investing in production features. Establish baseline latency and identify initial technical blockers.

**Delivers:**
- Simple HTML canvas capturing mousemove events
- FastAPI WebSocket server echoing coordinates
- pynput moving macOS cursor based on received coordinates
- Basic coordinate normalization (canvas → [0,1] → screen pixels)
- Permission checking with user-friendly error messages

**Addresses:**
- Must-have: Mouse capture, coordinate transmission, cursor movement
- Pitfall avoidance: Permission checking (pitfall #1), basic multi-monitor detection (pitfall #3)

**Tech stack:**
- Frontend: Vanilla HTML + Canvas + JavaScript
- Backend: FastAPI + WebSocket + pynput
- Protocol: JSON with {x, y, timestamp} messages

**Research flags:** Standard patterns, skip research-phase (all components well-documented)

### Phase 2: Retina/HiDPI Support
**Rationale:** Must handle Retina displays correctly before multi-user testing. Coordinate bugs compound quickly and are harder to debug later. Builds on Phase 1 coordinate foundation.

**Delivers:**
- ResizeObserver-based canvas sizing with devicePixelRatio detection
- Automatic ctx.scale(dpr, dpr) normalization
- Coordinate transformation accounting for canvas buffer vs display size
- Monitor DPI change detection (matchMedia listener)
- Validation that clicks map correctly on 2x displays

**Addresses:**
- Pitfall avoidance: Retina scaling errors (pitfall #7)

**Tech stack:**
- Browser: ResizeObserver, devicePixelRatio, matchMedia
- Same backend as Phase 1

**Research flags:** Standard patterns (well-documented in WebGL/Canvas communities)

### Phase 3: Connection Reliability & Latency Optimization
**Rationale:** After core functionality works, optimize for production use. Latency and reliability are critical for usability (unusable if >100ms lag).

**Delivers:**
- WebSocket heartbeat/ping-pong mechanism (detect stale connections)
- Client-side throttling with requestAnimationFrame
- Connection recovery on disconnect (exponential backoff retry)
- Latency metrics (measure round-trip time)
- Performance monitoring (messages/sec, event loop delay)

**Addresses:**
- Should-have: Sub-50ms latency, graceful degradation
- Pitfall avoidance: Event flooding (pitfall #5), memory leaks (pitfall #4)

**Tech stack:**
- Frontend: requestAnimationFrame throttling, WebSocket reconnect logic
- Backend: FastAPI heartbeat task, ConnectionManager cleanup patterns

**Research flags:** Standard patterns for WebSocket heartbeat, throttling well-documented

### Phase 4: Multi-Monitor Support
**Rationale:** Deferred until core single-monitor experience is solid. Adds significant complexity with coordinate offset calculation and Window Management API permission.

**Delivers:**
- Window Management API integration (getScreenDetails)
- Per-screen coordinate offset calculation
- User permission flow for window-management
- Fallback to single-monitor if permission denied
- Screen selection UI (which monitor to control)

**Addresses:**
- Should-have: Multi-monitor support
- Pitfall avoidance: Multi-monitor coordinate complexity (pitfall #3)

**Tech stack:**
- Browser: Window Management API (Chromium-only, requires permission)
- Backend: Screen enumeration, coordinate offset mapping

**Research flags:** Window Management API is evolving spec, may need deeper research during planning

### Phase 5: Production Deployment Readiness
**Rationale:** After core features work, prepare for real-world usage with proper deployment, monitoring, and scaling.

**Delivers:**
- Gunicorn + Uvicorn multi-worker deployment
- Nginx reverse proxy with WebSocket support
- Health check endpoint
- Prometheus metrics (connections, latency, messages)
- Static file serving for frontend
- Docker containerization

**Addresses:**
- Production deployment patterns from FastAPI research
- Scaling beyond single process

**Tech stack:**
- Deployment: Gunicorn, Uvicorn workers, Nginx
- Monitoring: Prometheus metrics, health checks
- Infrastructure: Docker, static file serving

**Research flags:** Standard FastAPI deployment patterns, well-documented

### Phase Ordering Rationale

**Why this order:**
- Phase 1 establishes core data flow (highest risk, must validate early)
- Phase 2 fixes Retina before bugs compound (Retina users are common, blocking)
- Phase 3 optimizes latency after correctness proven (premature optimization avoided)
- Phase 4 adds multi-monitor after single-monitor solid (complexity contained)
- Phase 5 productionizes after features complete (infrastructure deferred appropriately)

**Dependency chain:**
- Phase 2 depends on Phase 1 coordinate system
- Phase 3 depends on Phase 1 WebSocket foundation
- Phase 4 depends on Phase 2 coordinate transformation patterns
- Phase 5 depends on all prior phases being feature-complete

**Pitfall avoidance:**
- Permissions checked in Phase 1 (prevents silent failures)
- Retina handled in Phase 2 (prevents coordinate bugs)
- Connection reliability in Phase 3 (prevents memory leaks, event flooding)
- Multi-monitor isolated in Phase 4 (complexity contained)

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 4 (Multi-Monitor):** Window Management API is Chromium-only with evolving spec, may need fallback research for Firefox/Safari
- **Phase 5 (Production):** May need Docker networking research if WebSocket proxying issues arise

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** All components have official documentation (Canvas, FastAPI WebSocket, pynput)
- **Phase 2:** ResizeObserver and devicePixelRatio well-documented in MDN/WebGL resources
- **Phase 3:** WebSocket heartbeat and throttling are established patterns with many examples

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified compatible with Python 3.12, active maintenance, official docs |
| Features | HIGH | MVP feature set is minimal and all components individually proven |
| Architecture | HIGH | Three-layer pattern (browser/server/desktop) is straightforward with clear boundaries |
| Pitfalls | HIGH | All critical pitfalls documented with prevention strategies from official sources |

**Overall confidence:** HIGH

All four research areas converged on well-documented, actively maintained technologies with clear integration patterns. The main unknowns are latency performance (mitigated by JSON MVP with binary upgrade path) and macOS permission UX on Sequoia (mitigated by permission checking and clear prompts).

### Gaps to Address

**During Phase 1 planning:**
- Exact JSON message schema (define {x, y, timestamp} structure)
- macOS permission checking implementation (test actual detection method)
- Coordinate validation ranges (validate [0,1] bounds on both sides)

**During Phase 3 planning:**
- Latency targets (define acceptable thresholds: <50ms? <100ms?)
- Throttle rate tuning (how many events/sec is sustainable?)
- Binary protocol migration strategy (if JSON proves too slow)

**During Phase 4 planning:**
- Fallback strategy for non-Chromium browsers (Firefox/Safari lack Window Management API)
- Multi-monitor coordinate testing (need access to multi-monitor Mac setup)

**During Phase 5 planning:**
- Nginx WebSocket proxy configuration (verify WebSocket upgrade headers)
- Redis Pub/Sub integration (if multi-client broadcasting needed)

## Sources

### Primary (HIGH confidence)

**macOS input control:**
- [pynput PyPI](https://pypi.org/project/pynput/) - Official package, version compatibility
- [pynput Documentation](https://pynput.readthedocs.io/) - API reference, examples
- [PyAutoGUI Documentation](https://pyautogui.readthedocs.io/) - Fallback library reference
- [PyObjC Documentation - Quartz](https://pyobjc.readthedocs.io/en/latest/apinotes/Quartz.html) - Low-level macOS APIs
- [Apple Developer - CGEvent](https://developer.apple.com/documentation/coregraphics/cgevent) - Official macOS APIs

**FastAPI WebSocket:**
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - Official documentation
- [Starlette WebSocket Documentation](https://www.starlette.dev/websockets/) - Underlying implementation
- [FastAPI Exceptions Reference](https://fastapi.tiangolo.com/reference/exceptions/) - WebSocketException details
- [FastAPI Server Workers](https://fastapi.tiangolo.com/deployment/server-workers/) - Production deployment
- [websockets library - Keepalive](https://websockets.readthedocs.io/en/stable/topics/keepalive.html) - Heartbeat patterns

**Canvas input:**
- [MDN - Element: mousemove event](https://developer.mozilla.org/en-US/docs/Web/API/Element/mousemove_event) - Official event spec
- [MDN - KeyboardEvent](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent) - Keyboard event reference
- [MDN - Touch events](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events) - Touch event spec
- [MDN - Coordinate systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems) - Official coordinate system reference
- [WebAIM: Keyboard Accessibility - Tabindex](https://webaim.org/techniques/keyboard/tabindex) - Accessibility standards

**Coordinate mapping:**
- [MDN Coordinate Systems](https://developer.mozilla.org/en-US/docs/Web/API/CSSOM_view_API/Coordinate_systems) - Official spec
- [MDN devicePixelRatio](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio) - Retina handling
- [Khronos WebGL HandlingHighDPI](https://wikis.khronos.org/webgl/HandlingHighDPI) - Authoritative DPI guide
- [MDN Multi-screen Origin](https://developer.mozilla.org/en-US/docs/Web/API/Window_Management_API/Multi-screen_origin) - Multi-monitor spec
- [Chrome Window Management API](https://developer.chrome.com/docs/capabilities/web-apis/window-management) - Official API docs

### Secondary (MEDIUM confidence)

**Community guides and tutorials:**
- [Building Real-Time Applications with FastAPI WebSockets (2025)](https://dev-faizan.medium.com/building-real-time-applications-with-fastapi-websockets-a-complete-guide-2025-40f29d327733) - Recent patterns
- [Advanced WebSocket Architectures in FastAPI](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401) - Performance patterns
- [Handling mouse input events for a HTML canvas game](https://stephendoddtech.com/blog/game-design/mouse-event-listener-input-html-canvas) - Canvas event patterns
- [Ensuring Canvas Looks Good on Retina](https://www.kirupa.com/canvas/canvas_high_dpi_retina.htm) - Retina scaling guide
- [Working with the Mouse | KIRUPA](https://www.kirupa.com/canvas/working_with_the_mouse.htm) - Canvas mouse interaction

**Performance and optimization:**
- [10 Common FastAPI Mistakes That Hurt Performance](https://medium.com/@connect.hashblock/10-common-fastapi-mistakes-that-hurt-performance-and-how-to-fix-them-72b8553fe8e7) - Pitfall catalog
- [How to Handle Large Scale WebSocket Traffic](https://hexshift.medium.com/how-to-handle-large-scale-websocket-traffic-with-fastapi-9c841f937f39) - Scaling patterns

### Tertiary (LOW confidence)

- [Window Management API browser support](https://caniuse.com/window-management) - Current browser support matrix (evolving spec)
- [pynput macOS Sequoia permission behavior](https://github.com/moses-palmer/pynput/issues/389) - Community-reported permission issues (needs validation)

---

**Research completed:** 2026-02-09
**Ready for roadmap:** Yes

**Files synthesized:**
- `.planning/research/macos-input-control.md` - macOS automation library analysis
- `.planning/research/fastapi-websocket.md` - WebSocket server implementation patterns
- `.planning/research/canvas-input.md` - Browser input capture techniques
- `.planning/research/coordinate-mapping.md` - Browser-to-screen coordinate transformation

**Next steps:**
- Roadmapper agent can use this summary to structure detailed roadmap phases
- Phase 1 planning can begin immediately with well-defined scope
- Research flags indicate which phases may need `/gsd:research-phase` during execution
