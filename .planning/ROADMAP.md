# Roadmap: whip

## Overview

The whip MVP roadmap builds browser-to-macOS remote control incrementally over 5 phases. We start by establishing core infrastructure (FastAPI WebSocket server), then layer in browser input capture (canvas events), macOS control integration (pynput), accurate coordinate mapping (browser to screen), and finish with setup documentation and polish. Each phase delivers a coherent, testable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Core Infrastructure** - FastAPI server, WebSocket, static files, message protocol
- [x] **Phase 2: Browser Input Capture** - Canvas interface capturing mouse and keyboard events
- [ ] **Phase 3: macOS Control Integration** - Mouse and keyboard control via pynput
- [ ] **Phase 4: Coordinate Mapping** - Accurate browser-to-screen coordinate transformation
- [ ] **Phase 5: Setup & Documentation** - Installation instructions, permissions, README polish

## Phase Details

### Phase 1: Core Infrastructure
**Goal**: Web server running with WebSocket endpoint accepting connections and serving static files
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. FastAPI server starts and binds to 0.0.0.0 on local network
  2. Browser can connect to server and load HTML page
  3. WebSocket connection establishes between browser and server
  4. Server receives test messages from browser and echoes them back
  5. Server handles disconnects gracefully without crashing
**Plans:** 3 plans

Plans:
- [x] 01-01-PLAN.md — Project setup and FastAPI server with static files (port 9447)
- [x] 01-02-PLAN.md — WebSocket endpoint with JSON message protocol and echo
- [x] 01-03-PLAN.md — Smart event queue with mouse dedup and keyboard FIFO

### Phase 2: Browser Input Capture
**Goal**: Full-screen canvas captures all mouse and keyboard activity and transmits to server
**Depends on**: Phase 1 (requires WebSocket connection)
**Requirements**: FRONT-01, FRONT-02, FRONT-03, FRONT-04, FRONT-05, FRONT-06, FRONT-07
**Success Criteria** (what must be TRUE):
  1. Blank canvas fills entire browser window
  2. Canvas captures mouse movements and sends coordinates in real-time
  3. Canvas captures left/right/middle mouse clicks and sends button events
  4. Canvas captures keyboard presses and sends key codes
  5. Context menus and text selection are prevented on canvas
  6. Connection status indicator shows connected/disconnected state
**Plans:** 2 plans

Plans:
- [x] 02-01-PLAN.md — Full-screen canvas with mouse movement and click capture
- [x] 02-02-PLAN.md — Keyboard capture and default behavior prevention

### Phase 3: macOS Control Integration
**Goal**: Server controls macOS cursor and keyboard based on received events
**Depends on**: Phase 2 (requires input events from browser)
**Requirements**: MACOS-01, MACOS-02, MACOS-03, MACOS-04, MACOS-05, MACOS-06
**Success Criteria** (what must be TRUE):
  1. Server moves macOS cursor when receiving mouse position events
  2. Server triggers mouse clicks (left/right/middle) on host system
  3. Server sends keyboard key press and release events to macOS
  4. Server checks for Accessibility permissions on startup
  5. Server displays clear error message if permissions are missing
  6. User can grant permissions and server works after permission granted
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Permission checking and pynput controller modules
- [ ] 03-02-PLAN.md — Event consumer integration with human verification

### Phase 4: Coordinate Mapping
**Goal**: Browser coordinates map accurately to screen pixels across different resolutions and displays
**Depends on**: Phase 3 (requires cursor control working)
**Requirements**: COORD-01, COORD-02, COORD-03, COORD-04, COORD-05
**Success Criteria** (what must be TRUE):
  1. Browser sends normalized coordinates (0-1 range) instead of pixel values
  2. Server detects macOS screen resolution and stores it
  3. Server maps normalized coordinates to absolute screen pixels correctly
  4. Coordinate mapping works accurately on Retina/HiDPI displays
  5. Clicking corners of canvas moves cursor to corners of screen
**Plans**: TBD

Plans:
- [ ] TBD (will be created during planning)

### Phase 5: Setup & Documentation
**Goal**: User can install, configure, and run whip following clear documentation
**Depends on**: Phase 4 (requires working functionality to document)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, SETUP-05
**Success Criteria** (what must be TRUE):
  1. README includes step-by-step instructions for enabling macOS Accessibility
  2. README includes instructions for installing dependencies with uv
  3. README includes instructions for starting the server
  4. README includes the URL for accessing the web interface
  5. Project includes pyproject.toml with all required dependencies listed
**Plans**: TBD

Plans:
- [ ] TBD (will be created during planning)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Infrastructure | 3/3 | Complete | 2026-02-09 |
| 2. Browser Input Capture | 2/2 | Complete | 2026-02-09 |
| 3. macOS Control Integration | 0/2 | Planned | - |
| 4. Coordinate Mapping | 0/? | Not started | - |
| 5. Setup & Documentation | 0/? | Not started | - |
