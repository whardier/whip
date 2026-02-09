# whip

## What This Is

A minimal web-based remote control for macOS that captures mouse movements and keyboard input from a web browser canvas and relays them to the host computer. Users access a blank canvas in their browser, and any mouse/keyboard activity on that canvas controls the host machine's cursor and keyboard in real-time via WebSocket.

## Core Value

Reliable real-time relay of mouse position and keyboard input from web browser to host macOS system.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Web server serves blank canvas interface accessible on local network
- [ ] Canvas captures all mouse movements and sends absolute coordinates via WebSocket
- [ ] Canvas captures keyboard input and sends key events via WebSocket
- [ ] Python backend receives WebSocket events and translates to macOS system events
- [ ] Absolute mouse positioning maps webapp coordinates to host screen coordinates
- [ ] Mouse clicks (left/right/middle) are captured and replayed on host
- [ ] Setup instructions include enabling macOS accessibility permissions for the app

### Out of Scope

- Advanced features (screen sharing, clipboard sync, audio) — MVP focused on basic input relay
- Cross-platform support (Windows/Linux) — macOS only for initial version
- Authentication/security — local network trust model for MVP
- Mobile-optimized interface — desktop browser focus
- Relative mouse movement — absolute positioning only
- Complex keyboard combinations or shortcuts — simple key replay only

## Context

This is a new MVP project starting from scratch. The goal is to prove the core concept of browser-to-host input relay works reliably before adding features.

**Technical environment:**
- Host machine: macOS
- May run in iTerm2 with specific accessibility permissions
- Local network deployment (0.0.0.0 binding)
- No existing codebase — greenfield project

**Key challenge:**
- macOS accessibility APIs require proper permissions
- Need to translate web coordinates to absolute screen positions
- WebSocket must handle real-time input with minimal latency

## Constraints

- **Tech stack**: Python 3.12, FastAPI, vanilla HTML/CSS/JS — per user preference for simplicity
- **Platform**: macOS only — accessibility APIs are platform-specific
- **Scope**: MVP feature set — absolute mouse + simple keyboard only
- **Deployment**: Local network — not designed for internet-facing deployment
- **Dependencies**: Use `uv` for Python package management

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI for backend | Modern async framework with excellent WebSocket support and docs | — Pending |
| Vanilla HTML/CSS/JS for frontend | No build step, simple for MVP, easy to iterate | — Pending |
| Local network access (0.0.0.0) | Allow access from other devices on LAN for flexibility | — Pending |
| Support clicks + movement | More useful MVP than movement-only | — Pending |
| Absolute positioning only | Simpler to implement and reason about than relative | — Pending |

---
*Last updated: 2026-02-09 after initial project definition*
