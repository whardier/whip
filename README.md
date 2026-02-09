# whip

Web-based remote control for macOS - relay mouse and keyboard input from any browser to your Mac.

## Overview

whip is a minimal web application that captures mouse movements and keyboard input from a web browser and relays them to the host macOS system in real-time. Access a blank canvas in your browser from any device on your local network, and control your Mac's cursor and keyboard as if you were sitting at the machine.

Use cases include controlling your Mac from a phone or tablet, assistive technology applications, and remote demonstrations where you need precise input control.

## Requirements

- macOS (Ventura or later recommended)
- Python 3.12 or later
- uv package manager

**Important**: macOS Sequoia 15.0+ resets Accessibility permissions monthly and after every system reboot. You will need to re-grant permissions periodically.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd whip

# Install dependencies with uv
uv sync
```

## macOS Accessibility Permissions

**This step is critical.** whip requires Accessibility permissions to control the mouse and keyboard via the pynput library.

### Why permissions are needed

macOS protects against unauthorized input control by requiring explicit permission for applications to programmatically control the mouse and keyboard. Without these permissions, the server will start but input control will not work.

### Granting permissions

1. Open **System Settings**
2. Navigate to **Privacy & Security** → **Accessibility**
3. Click the lock icon and authenticate with your password
4. Enable the application that is running the whip server:
   - **Terminal** (if running from default Terminal app)
   - **VS Code** (if running from VS Code integrated terminal)
   - **PyCharm** (if running from PyCharm)
   - **iTerm2** (if using iTerm2)
   - Or whichever application is executing the Python process

### Important notes

- The server will start without permissions but display a warning message
- Input control will not function until permissions are granted
- After granting permissions, restart the server
- **macOS Sequoia 15.0+**: Accessibility permissions must be re-granted monthly and after every system reboot

## Running the Server

Start the whip server using uvicorn:

```bash
uv run uvicorn whip.main:app --host 0.0.0.0 --port 9447
```

The `--host 0.0.0.0` flag enables access from other devices on your local network (not just localhost).

## Accessing the Interface

### From the same machine

Open your browser and navigate to:

```
http://localhost:9447
```

### From other devices on your network

Find your Mac's local IP address:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Then access the interface from your phone, tablet, or another computer using:

```
http://<your-mac-ip>:9447
```

For example: `http://192.168.1.100:9447`

## How It Works

1. **Browser capture**: The web interface presents a full-screen canvas that captures all mouse movements, clicks, and keyboard input
2. **WebSocket relay**: Input events are sent in real-time over a WebSocket connection to the FastAPI server running on your Mac
3. **macOS control**: The server translates these events into system-level mouse and keyboard actions using the pynput library
4. **Coordinate mapping**: Browser coordinates are normalized and mapped to your screen resolution for accurate cursor positioning

The canvas uses absolute positioning, so clicking anywhere on the canvas moves your Mac's cursor to the corresponding screen location.

## Port Number

The default port is 9447, which spells "WHIP" on a phone keypad (9=W, 4=H, 4=I, 7=P).
