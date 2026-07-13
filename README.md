# SessionCountdown

Raspberry Pi-first race session countdown display with local-network timetable control.

## Project direction

- **Raspberry Pi:** primary display node and source of truth for the active countdown.
- **Windows laptop:** control station used through a web browser on the same Wi-Fi network.
- **Offline operation:** the Pi stores the latest timetable locally and continues running if the controller disconnects.
- **Local network:** no internet connection is required for timetable control.

## Initial source

This repository begins from the original standalone Python/CustomTkinter application. The next milestone will separate the display, timetable storage, API, and browser control interface while preserving the original behaviour as a reference.

## Planned architecture

```text
Windows laptop browser
        |
        | Local Wi-Fi (HTTP/WebSocket)
        v
Raspberry Pi API + timetable store
        |
        v
Fullscreen countdown display
```

## Development status

Initial project import in progress.
