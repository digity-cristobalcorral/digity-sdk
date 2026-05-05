---
eyebrow: Integrations
lede: A real-time web dashboard with 3D hand models, touch visualization, recording, and remote agent relay — all in one command.
---

## Installation

```bash
# Linux: system packages first
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
pip install "digity[viz]"

# Windows: no extra steps
pip install "digity[viz]"
```

## Launch

```bash
# Opens desktop window (requires pywebview)
digity-viz

# Open in system browser instead
digity-viz --browser

# Specify serial port explicitly
digity-viz --port /dev/ttyUSB0

# Fallback on Windows if CLI is not on PATH
python -m digity.viz
```

The server always starts at `http://127.0.0.1:5001/chiros/`.

## Dashboard pages

| Page | URL | Description |
|---|---|---|
| Viewer | `/chiros/` | Single 3D hand model animated live from glove data. |
| Multiview | `/chiros/multiview` | Side-by-side view of up to 200 hand instances. Add `?model=inspire&copies=4` to configure. |
| Record | `/chiros/record` | Record glove sessions to `~/digity-recordings/` as JSONL files. |
| Setup | `/chiros/setup` | Configure serial port, station name, recording directory, and agent tokens. |

## 3D hand models

The multiview page supports multiple hand models via the `?model=` query parameter:

| Model | Description |
|---|---|
| `inspire` | Inspire Hand (rigid GLB pieces, URDF kinematics). |
| `ability` | Ability Hand. |
| `schunk` | Schunk SVH hand. |
| `ultraleap` | Ultraleap hand skeleton. |
| `shadow` | Shadow Dexterous Hand. |
| `allegro` | Allegro Hand. |

Example URLs:

```
http://127.0.0.1:5001/chiros/multiview?model=inspire&copies=2
http://127.0.0.1:5001/chiros/multiview?model=shadow&copies=4
```

## Recording

Sessions are saved to `~/digity-recordings/<session_id>/`:

| File | Format | Contents |
|---|---|---|
| `meta.json` | JSON | Subject, task, hand side, station, start/end timestamps, frame count. |
| `recording.jsonl` | JSON Lines | One object per line: `{"ts": float, "side": ..., "sensors": [...]}`. Same structure as `GloveFrame` dict. |

## Agent relay (remote streaming)

The agent relay streams glove data from a local machine to a remote server over WebSocket:

```bash
# Start the dashboard with agent mode (streams to remote server)
digity-viz --agent --token YOUR_TOKEN

# Standalone agent (no local dashboard window)
digity-agent --token YOUR_TOKEN --url https://app.digity.de/chiros
```

Obtain a token from the Setup page (`/chiros/setup`) → Agent tokens section.

## Python API

```python
from digity.viz import start

# equivalent to: digity-viz --browser --port /dev/ttyUSB0
start(port="/dev/ttyUSB0", browser=True)
```

## Where to go next

- [Rerun viewer](integrations-rerun.md) — alternative 3D visualization with time-series charts.
- [System requirements](system-requirements.md) — Linux GTK dependency details.
