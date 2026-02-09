---
phase: 01-core-infrastructure
plan: 01
subsystem: core
tags: [infrastructure, fastapi, server, static-files]

dependency_graph:
  requires: []
  provides: [fastapi-server, static-file-serving, port-9447]
  affects: [all-subsequent-phases]

tech_stack:
  added:
    - FastAPI ~=0.115.0 (web framework with async support)
    - uvicorn[standard] ~=0.34.0 (ASGI server)
    - ruff ~=0.9.0 (linting)
    - pyright ~=1.1.0 (type checking)
  patterns:
    - src layout for Python package structure
    - Static file serving with StaticFiles mount
    - Root redirect to main interface

key_files:
  created:
    - pyproject.toml (project configuration)
    - src/whip/__init__.py (package marker)
    - src/whip/main.py (FastAPI application)
    - src/whip/__main__.py (module entry point)
    - static/index.html (web interface placeholder)
    - .python-version (Python 3.12 pin)
    - uv.lock (dependency lock file)
  modified: []

decisions:
  - choice: "Use uv for package management"
    rationale: "Modern, fast Python package manager with good dependency resolution"
    alternatives: ["pip + venv", "poetry"]
  - choice: "Port 9447 for server"
    rationale: "WHIP on phone keypad, memorable and avoids common ports"
    alternatives: ["8000", "8080"]
  - choice: "Bind to 0.0.0.0"
    rationale: "Allow access from other devices on local network"
    alternatives: ["127.0.0.1 (localhost only)"]
  - choice: "120 character line length"
    rationale: "Modern screens support wider lines, improves readability"
    alternatives: ["88 (Black default)", "100"]

metrics:
  duration_minutes: 3
  tasks_completed: 2
  commits: 2
  files_created: 7
  dependencies_added: 4
  completed_date: "2026-02-09"
---

# Phase 1 Plan 01: Project Setup and FastAPI Server Summary

**One-liner:** FastAPI server on port 9447 serving static HTML interface, with uv package management and Python 3.12 environment.

## What Was Built

Established the foundational Python project structure and web server infrastructure for the WHIP application. Set up a FastAPI server that binds to 0.0.0.0:9447 and serves static files from the `/static` endpoint, providing the base for browser-based remote control functionality.

## Tasks Completed

### Task 1: Initialize Python project with uv and dependencies
**Commit:** e6abf0d
**Files:** pyproject.toml, src/whip/__init__.py, .python-version, uv.lock

Set up Python 3.12 project with uv package manager, installed FastAPI ~=0.115.0 and uvicorn[standard] ~=0.34.0 for the web server, and configured development tools (ruff ~=0.9.0, pyright ~=1.1.0) with 120-character line length and basic type checking.

### Task 2: Create FastAPI server with static file serving
**Commit:** ede4039
**Files:** src/whip/main.py, src/whip/__main__.py, static/index.html

Created FastAPI application with StaticFiles mount at `/static`, implemented root endpoint redirecting to `/static/index.html`, and added basic HTML interface placeholder with connection status div for future WebSocket integration.

## Verification Results

All success criteria met:
- [x] FastAPI server starts on 0.0.0.0:9447 without errors
- [x] Static HTML page loads in browser and contains "WHIP" branding
- [x] Project structure follows Python best practices (src layout)
- [x] Dependencies installed and working (verified via `uv run python -c "import fastapi"`)
- [x] Server accessible from curl: `curl http://localhost:9447/static/index.html` returns HTML

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Python version mismatch**
- **Found during:** Task 1, dependency installation
- **Issue:** `.python-version` was set to 3.11 by uv init, but pyproject.toml required >=3.12
- **Fix:** Ran `uv python pin 3.12` to update .python-version to match requirement
- **Files modified:** .python-version
- **Commit:** e6abf0d (included in Task 1)

**2. [Rule 3 - Blocking] Added build system configuration**
- **Found during:** Task 2, module import testing
- **Issue:** `whip` module not importable - uv couldn't install package without build-system config
- **Fix:** Added `[build-system]` section to pyproject.toml with hatchling backend
- **Files modified:** pyproject.toml
- **Commit:** ede4039 (included in Task 2)

**3. [Rule 3 - Blocking] Removed default main.py file**
- **Found during:** Task 2, project structure setup
- **Issue:** uv init created default main.py in project root, conflicts with src layout
- **Fix:** Deleted root-level main.py as we use src/whip structure
- **Files modified:** main.py (deleted)
- **Commit:** ede4039 (included in Task 2)

## Technical Notes

### FastAPI Static Files
- StaticFiles mount resolves directory path at module load time
- Path resolution uses `Path("static").resolve()` from cwd (project root when running uvicorn)
- Serves files with proper MIME types, etags, and cache headers

### Package Structure
- Using src layout prevents accidental imports from development directory
- Module can be run via `uv run python -m whip` or `uv run uvicorn whip.main:app`
- hatchling automatically handles src/ discovery for package installation

### Port Selection
- Port 9447 chosen to spell "WHIP" on phone keypad (9=W, 4=H, 4=I, 7=P)
- Binding to 0.0.0.0 allows connections from other devices on local network
- No authentication yet - relying on local network trust model for MVP

## Next Steps

This plan provides the foundation for:
- **Plan 01-02:** WebSocket endpoint implementation with JSON message protocol
- **Plan 01-03:** Smart event queue for mouse/keyboard input handling
- **Phase 2:** Browser-based canvas input capture
- **Phase 3:** macOS control integration via pynput

The server is ready to accept WebSocket connections and serve the interactive canvas interface.

## Dependencies for Future Plans

**Provides to downstream:**
- Working FastAPI server on port 9447
- Static file serving capability for HTML/CSS/JS
- Python 3.12 environment with async support
- Development tooling (ruff, pyright)

**Blocks if unavailable:**
- All subsequent plans require this server foundation
- WebSocket endpoint (Plan 01-02) mounts on this app instance
- Browser interface (Phase 2) served via this static endpoint

## Self-Check: PASSED

**Files verification:**
```
FOUND: /Users/spencersr/tmp/whip/pyproject.toml
FOUND: /Users/spencersr/tmp/whip/src/whip/__init__.py
FOUND: /Users/spencersr/tmp/whip/src/whip/main.py
FOUND: /Users/spencersr/tmp/whip/src/whip/__main__.py
FOUND: /Users/spencersr/tmp/whip/static/index.html
FOUND: /Users/spencersr/tmp/whip/.python-version
FOUND: /Users/spencersr/tmp/whip/uv.lock
```

**Commits verification:**
```
FOUND: e6abf0d (Task 1: chore(01-01): initialize Python project)
FOUND: ede4039 (Task 2: feat(01-01): create FastAPI server)
```

**Runtime verification:**
```
✓ Server starts: uv run uvicorn whip.main:app --host 0.0.0.0 --port 9447
✓ Module import: uv run python -c "import fastapi; print(fastapi.__version__)" → 0.115.14
✓ Static file: curl http://localhost:9447/static/index.html → contains "WHIP"
✓ Linting: uv run ruff --version → ruff 0.9.10
```

All files created, all commits present, server verified working.
