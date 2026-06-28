# kast-c2

> ⚠️ **Educational purposes only.** This project was built to study offensive security concepts — C2 architecture, socket communication, persistence mechanisms, and data exfiltration techniques. Do not use against systems you do not own or have explicit permission to test. The author takes no responsibility for misuse.

---

A Python-based Remote Access Trojan with a C2 (Command & Control) infrastructure, built as a cybersecurity learning project. This is a work in progress.

## Motivation

Understanding how offensive tools work is fundamental to defending against them. This project was built to study:

- How RATs establish and maintain connections to a C2 server
- How data is exfiltrated over raw sockets
- How malware persists across reboots via the Windows registry
- How a C2 server manages multiple victims and logs activity

## Architecture

> Diagram coming soon (Excalidraw asset)

The project has two sides:

**Client (`svchost.py`)** — runs on the victim machine. Connects back to the C2 server, collects system information, and waits for commands.

**Server (`server.py`)** — runs on the attacker machine. Accepts incoming connections, stores victim data in SQLite, and dispatches commands.

## Features

### Implemented
- [x] TCP socket-based C2 connection
- [x] System info collection (hostname, IP, OS, platform)
- [x] Windows registry persistence
- [x] Self-copy to `AppData` before registry entry
- [x] Screenshot capture and exfiltration
- [x] Keylogger (runs in parallel thread, dumps to hidden file)
- [x] Shell command execution with directory state
- [x] Audio recording
- [x] Self-destruction

### In progress
- [ ] Binary message protocol (type|size|extra header)
- [ ] Audio exfiltration via socket
- [ ] File download command
- [ ] C2 server (`server.py`) with SQLite persistence
- [ ] Reconnection logic

## Project Structure

```
kast-c2/
├── svchost.py      # RAT client (victim side)
├── server.py       # C2 server (attacker side) — WIP
├── db.py           # SQLite helpers
└── loot/           # Exfiltrated data (gitignored)
```

## Environment

Tested on Windows. Developed and studied in a controlled local lab using Docker with isolated networks.

---

*Part of a personal cybersecurity studies portfolio.*
