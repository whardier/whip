# Requirements: whip

**Defined:** 2026-02-09
**Core Value:** Reliable real-time relay of mouse position and keyboard input from web browser to host macOS system.

## v1 Requirements (MVP)

Requirements for initial working prototype. Browser-based remote control of host macOS system.

### Infrastructure

- [ ] **INFRA-01**: FastAPI web server starts and binds to 0.0.0.0 for local network access
- [ ] **INFRA-02**: Server serves static HTML/CSS/JS files for web interface
- [ ] **INFRA-03**: WebSocket endpoint accepts connections and maintains persistent connection
- [ ] **INFRA-04**: JSON message protocol defined for mouse and keyboard events
- [ ] **INFRA-05**: Server handles WebSocket disconnects gracefully with proper cleanup

### Frontend

- [ ] **FRONT-01**: HTML page loads with full-screen blank canvas
- [ ] **FRONT-02**: Canvas captures mouse movement events with offsetX/offsetY coordinates
- [ ] **FRONT-03**: Canvas captures mouse click events (left/right/middle button)
- [ ] **FRONT-04**: Canvas captures keyboard events (key down/up with key codes)
- [ ] **FRONT-05**: Canvas sends events to server via WebSocket in real-time
- [ ] **FRONT-06**: Canvas prevents default browser behaviors (context menu, text selection)
- [ ] **FRONT-07**: Canvas displays connection status indicator

### Coordinate Mapping

- [ ] **COORD-01**: Browser sends normalized coordinates (0-1 range) to server
- [ ] **COORD-02**: Server detects macOS screen resolution on startup
- [ ] **COORD-03**: Server maps normalized coordinates to absolute screen pixels
- [ ] **COORD-04**: Canvas handles Retina/HiDPI displays correctly (devicePixelRatio)
- [ ] **COORD-05**: Coordinate transformation maintains accuracy across different resolutions

### macOS Control

- [ ] **MACOS-01**: Server uses pynput library for mouse and keyboard control
- [ ] **MACOS-02**: Server moves mouse cursor to absolute screen coordinates
- [ ] **MACOS-03**: Server triggers mouse clicks (left/right/middle)
- [ ] **MACOS-04**: Server sends keyboard key press and release events
- [ ] **MACOS-05**: Server checks for macOS Accessibility permissions on startup
- [ ] **MACOS-06**: Server displays helpful error message if permissions not granted

### Setup & Documentation

- [ ] **SETUP-01**: README includes instructions for enabling macOS Accessibility permissions
- [ ] **SETUP-02**: README includes instructions for installing dependencies with uv
- [ ] **SETUP-03**: README includes instructions for running the server
- [ ] **SETUP-04**: README includes URL for accessing the web interface
- [ ] **SETUP-05**: Project includes requirements.txt or pyproject.toml for dependencies

## v2 Requirements

Deferred to future releases. Tracked but not in MVP scope.

### Performance

- **PERF-01**: Latency optimization to achieve <50ms end-to-end delay
- **PERF-02**: Event throttling to prevent overwhelming server with mousemove events
- **PERF-03**: Binary WebSocket protocol for reduced message size
- **PERF-04**: Connection pooling and efficient resource management

### Reliability

- **RELI-01**: WebSocket heartbeat/ping to detect stale connections
- **RELI-02**: Automatic reconnection on connection loss
- **RELI-03**: Error recovery for failed mouse/keyboard operations
- **RELI-04**: Connection status monitoring and metrics

### Multi-Monitor

- **MULTI-01**: Detection of multiple monitors and their layouts
- **MULTI-02**: Canvas selection of target monitor
- **MULTI-03**: Coordinate mapping across multiple screens
- **MULTI-04**: Window Management API integration for Chromium browsers

### Security

- **SEC-01**: Basic authentication for web interface access
- **SEC-02**: TLS/HTTPS support for encrypted communication
- **SEC-03**: Rate limiting to prevent abuse
- **SEC-04**: Input validation and sanitization

## Out of Scope

Explicitly excluded from current project. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Screen sharing / visual feedback | MVP focused on input relay only, not display capture |
| Clipboard sync | Adds complexity, defer to future version |
| File transfer | Not core to input control value proposition |
| Audio relay | Out of scope for input control tool |
| Windows/Linux support | macOS-only for MVP, platform-specific APIs |
| Relative mouse movement | Absolute positioning simpler and sufficient for MVP |
| Mobile app | Desktop browser focus, mobile UI complexity not justified |
| Modifier key combinations (Cmd+C, etc.) | Simple key replay only, complex shortcuts deferred |
| Gaming-grade latency (<10ms) | MVP targets usability, not competitive gaming |
| Production-ready deployment (Nginx, Docker) | Local development server sufficient for MVP |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| INFRA-04 | Phase 1 | Pending |
| INFRA-05 | Phase 1 | Pending |
| FRONT-01 | Phase 2 | Pending |
| FRONT-02 | Phase 2 | Pending |
| FRONT-03 | Phase 2 | Pending |
| FRONT-04 | Phase 2 | Pending |
| FRONT-05 | Phase 2 | Pending |
| FRONT-06 | Phase 2 | Pending |
| FRONT-07 | Phase 2 | Pending |
| MACOS-01 | Phase 3 | Pending |
| MACOS-02 | Phase 3 | Pending |
| MACOS-03 | Phase 3 | Pending |
| MACOS-04 | Phase 3 | Pending |
| MACOS-05 | Phase 3 | Pending |
| MACOS-06 | Phase 3 | Pending |
| COORD-01 | Phase 4 | Pending |
| COORD-02 | Phase 4 | Pending |
| COORD-03 | Phase 4 | Pending |
| COORD-04 | Phase 4 | Pending |
| COORD-05 | Phase 4 | Pending |
| SETUP-01 | Phase 5 | Pending |
| SETUP-02 | Phase 5 | Pending |
| SETUP-03 | Phase 5 | Pending |
| SETUP-04 | Phase 5 | Pending |
| SETUP-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27/27 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-02-09*
*Last updated: 2026-02-09 after roadmap creation*
