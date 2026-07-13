# SessionCountdown

Raspberry Pi-first race-session countdown display with browser control over the same local Wi-Fi network.

## Architecture

- **Raspberry Pi:** owns the timetable, stores it locally, serves the control page, and runs the display.
- **Windows laptop:** opens the control page in a browser and sends timetable changes to the Pi.
- **Offline-safe:** after a timetable has been saved, the Pi continues independently if the laptop disconnects.
- **No cloud required:** HTTP and WebSocket traffic stays on the local network.

## Current milestone: Pi network foundation

The repository now includes:

- fullscreen browser display at `/display`
- timetable editor at `/`
- JSON timetable API
- WebSocket live updates
- atomic local timetable storage
- Raspberry Pi install and start scripts
- systemd service template

## Raspberry Pi installation

```bash
git clone https://github.com/grrbaa/SessionCountdown.git
cd SessionCountdown
chmod +x scripts/install_pi.sh
./scripts/install_pi.sh
./scripts/start_pi.sh
```

Open from the Windows laptop:

```text
http://session-countdown.local:8080/
```

Open on the Raspberry Pi display:

```text
http://localhost:8080/display
```

If mDNS is unavailable, replace `session-countdown.local` with the Pi's IP address.

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
uvicorn session_countdown.main:app --reload --host 0.0.0.0 --port 8080
```

## Next milestones

1. Import the original visual identity and circuit assets.
2. Add drag-and-drop session ordering and bulk delay controls.
3. Add password/PIN protection for timetable editing.
4. Add Chromium kiosk autostart on Raspberry Pi.
5. Add import from RaceOps and timetable/run-sheet files.
