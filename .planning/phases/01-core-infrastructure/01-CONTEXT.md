# Phase 1: Core Infrastructure - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

FastAPI server that serves static HTML/CSS/JS files and accepts WebSocket connections for real-time bidirectional communication. This is the foundation layer - no mouse control or input capture yet, just the communication infrastructure that other phases build upon.

</domain>

<decisions>
## Implementation Decisions

### Server Configuration
- Default port: **9447** (WHIP on phone keypad - aligns with project name)
- Bind to 0.0.0.0 for local network access
- Server listens on startup with clear output showing connection URL

### Event Queue Architecture (Smart Queue - Built in Phase 1)
- **Mouse movement deduplication:** When new `mouse_move` event arrives, **replace ALL pending mouse_move events** in queue with the latest position
- **Keyboard event guarantee:** Strict FIFO order - every `key_down` and `key_up` processed in exact order received, no skipping ever
- **Async/sync bridge:** Queue-based architecture for handling async WebSocket → sync pynput bridge (implemented in Phase 3, but queue built now)
- Only process most up-to-date mouse position to minimize replay lag
- Queue must provide visibility into backlog for monitoring

### Tooling & Development Standards
- **Package management:** `uv` (Python 3.12)
- **Linting/formatting:** `ruff`
- **Type checking:** `pyright`
- **Line length:** 120 characters
- **Dependency pinning:** Use `~=` for patch version compatibility (e.g., `fastapi~=0.109.0`)

### Claude's Discretion
- Message protocol structure (type + data pattern vs flat structure)
- Static file directory structure (simple flat vs organized subdirs)
- Logging strategy and debug output
- Error handling for WebSocket errors and malformed messages
- Connection limit policy (how many simultaneous browser connections)

</decisions>

<specifics>
## Specific Ideas

- Port 9447 chosen specifically to encode "WHIP" on phone keypad (W=9, H=4, I=4, P=7)
- Smart queue behavior is critical for performance - mouse moves must not accumulate lag, keyboard must never drop events
- Queue architecture designed upfront even though pynput integration happens in Phase 3

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 01-core-infrastructure*
*Context gathered: 2026-02-09*
