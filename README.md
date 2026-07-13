# SessionCountdown

Windows-master race-session controller with Raspberry Pi display clients.

## Roles

- **Windows laptop:** owns events, PDF imports, timetable editing and live control.
- **Raspberry Pi:** fullscreen display only. It caches the latest schedule and reconnects automatically.

## Start the Windows controller

```bat
scripts\start_controller_windows.bat
```

Open `http://localhost:8080`. The controller listens on the laptop's network interfaces so Pi displays can connect.

## Start a Pi display

```bash
sudo apt update
sudo apt install -y chromium
chmod +x scripts/start_display_pi.sh
DISPLAY_ID="Garage" ./scripts/start_display_pi.sh http://LAPTOP-IP:8080
```

Find the laptop IP with `ipconfig`. Both machines must be on the same Wi-Fi and Windows Firewall must allow Python on private networks.

## PDF import

The controller can read a schedule PDF, detect supported categories, then extract the selected category into an editable timetable. Procedure milestones are optional: schedules without trolley, pit-lane or board details still import their ordinary sessions.

The first validated importer format is the 2026 Paul Ricard GT Sport schedule. It extracts E4 practice, qualifying and race sessions, plus available race-procedure milestones.
