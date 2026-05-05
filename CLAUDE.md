# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Business context

Digity sells a sensorized exohand (glove with embedded sensors).
Clients receive the hardware and need software to collect the sensor data in their own Python programs.
This SDK is the product they install: `pip install digity`.

There are two tiers:
1. **digity SDK** (core, no extras) — Python library to collect raw sensor data
2. **digity viz** (optional, `pip install digity[viz]`) — real-time web dashboard with 3D hand rendering, recording, and agent relay

The SDK must work standalone — no other Digity software required on the client machine.

---

## Platform requirements for `digity[viz]`

**Linux (Debian/Ubuntu):** pywebview requires GTK and Python GObject bindings, which must come from the system package manager — they are not on PyPI. Install **before** creating any venv:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Then either:
- Create the venv normally and `pip install "digity[viz]"`, **or**
- Use `python3 -m venv .venv --system-site-packages` so the venv inherits `gi`.

**Linux headless (no display):** the server still starts and prints the URL. Access via SSH tunnel:
```bash
ssh -L 5001:127.0.0.1:5001 user@server
# open http://localhost:5001/chiros/ locally
```

**Windows:** no extra system deps. If `digity-viz` / `digity-agent` are not found on PATH (common with Windows Store Python), use `python -m digity.viz` as a drop-in replacement.

---

## Development commands

```bash
# Install in editable mode with all extras
pip install -e ".[viz,agent]"

# Run the live example (glove must be plugged in)
python examples/basic.py
python examples/basic.py /dev/ttyUSB0   # explicit port, Linux
python examples/basic.py COM3           # explicit port, Windows

# Run the dashboard
digity-viz                              # opens desktop window (requires pywebview)
digity-viz --browser                    # open in system browser
digity-viz --port /dev/ttyUSB0          # explicit serial port
python -m digity.viz                    # fallback when CLI is not on PATH

# Start the dashboard from Python (equivalent to digity-viz --browser)
from digity.viz import start
start(port="/dev/ttyUSB0", browser=True)

# Stream glove to a remote dashboard
digity-viz --agent --token TOKEN
digity-agent --token TOKEN --url https://app.digity.de/chiros

# Lint (ruff is configured in pyproject.toml, line-length=100, rules E/F/W/I)
ruff check src/

# Build a distribution package
pip install build twine
python -m build
twine upload dist/*
```

No automated tests exist yet.

When releasing: bump `version` in **both** `pyproject.toml` and `src/digity/__init__.py`.

---

## Package structure

```
digity-sdk/
├── pyproject.toml              — PyPI metadata, optional-deps: viz, agent
├── src/
│   └── digity/
│       ├── __init__.py         — public API re-exports
│       ├── _types.py           — dataclasses: GloveFrame, AnglesSensor, ImuSensor, TouchSensor
│       ├── _humi.py            — HUMI binary protocol parser (ESP32 → Python dicts)
│       ├── _serial.py          — SerialReader thread + find_glove_port() auto-detection
│       ├── _stream.py          — GloveStream class (serial/ZMQ modes, dict→dataclass)
│       ├── _publisher.py       — GlovePublisher (ZMQ PUB socket broadcaster)
│       └── viz/
│           ├── __init__.py     — digity.viz public API + CLI entry points
│           ├── __main__.py     — python -m digity.viz support
│           ├── _server.py      — Flask + SocketIO dashboard server
│           ├── _agent.py       — agent relay client (streams local glove to remote server)
│           ├── templates/      — Jinja2 HTML templates (viewer, multiview, record, setup, users, login)
│           └── static/         — JS (Three.js, socket.io, hand builders), GLB models, images
└── examples/
    └── basic.py                — plug in glove, run this, see live data
```

Files prefixed with `_` are internal. Clients import only from `digity` and `digity.viz`.

---

## How it fits into the full system

```
[ESP32 glove firmware]
        │  USB cable (serial, 921600 baud, HUMI binary protocol)
        ▼
[Client machine]
  digity SDK (_serial.py reads bytes → _humi.py decodes → GloveFrame objects)
        │
        ├──▶ client's Python code  (data collection, research, robotics)
        ├──▶ GlovePublisher  (ZMQ PUB — local network subscribers)
        └──▶ digity.viz._server  (Flask dashboard, recording, ZMQ relay)
                │
                └──▶ digity.viz._agent  (WebSocket relay to remote cloud/server)
```

Optional remote mode: `GloveStream(host="192.168.1.10")` receives frames over ZMQ from a machine running glove-core, bypassing `_serial.py` and `_humi.py`.

---

## Public API

```python
from digity import GloveStream, GlovePublisher, AnglesSensor, ImuSensor, TouchSensor, GloveNotFoundError, Sensor

# Serial mode — glove plugged into this machine (default)
with GloveStream() as stream:
    for frame in stream:                   # blocks until next frame (~50 Hz)
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                print(sensor.finger, sensor.samples[-1].angles_deg)

# ZMQ mode — glove on remote machine running glove-core
GloveStream(host="192.168.1.10")

# Publish over ZMQ for local subscribers (alongside custom processing)
with GlovePublisher() as pub:
    with GloveStream() as stream:
        for frame in stream:
            pub.publish(frame)

# Standalone publisher (no custom processing needed)
with GlovePublisher() as pub:
    pub.run()   # blocks; Ctrl+C to stop
```

Always use `isinstance(sensor, AnglesSensor)` to branch — do not compare string type names.

---

## Data types

`GloveFrame` fields:

| Field | Type | Meaning |
|---|---|---|
| `ts` | float | host timestamp, seconds since epoch |
| `side` | str | `"right"` or `"left"` |
| `group` | str | `"hand"` or `"arm"` |
| `node_id` | int | PCB node number on the glove |
| `seq` | int | packet counter 0–65535, wraps |
| `sensors` | list | list of sensor objects (see below) |

| Class | Fields |
|---|---|
| `AnglesSensor` | `finger` (int), `com` (int), `samples: list[AnglesSample]` |
| `AnglesSample` | `ts_us` (int, µs), `angles_deg` (list of floats) |
| `ImuSensor` | `finger`, `com`, `samples: list[ImuSample]` |
| `ImuSample` | `ts_us`, `acc: tuple[int,int,int]` (raw i16), `gyro: tuple[int,int,int]` (raw i16) |
| `TouchSensor` | `finger`, `com`, `ts_us`, `channels` (6 floats 0..1), `channels_raw` (6 ints 0..4095) |

`Sensor = Union[AnglesSensor, ImuSensor, TouchSensor]` is exported for type annotations.

---

## How the core code works (internal flow)

### Step 1 — Auto-detect USB port (`_serial.py:find_glove_port`)
Scans `serial.tools.list_ports` for known USB-serial chips:
- VIDs: `1A86` (CH340/CH341), `10C4` (CP210x), `0403` (FTDI), `303A` (ESP32 built-in)
- Keywords in description: CH340, CH341, CP210, FTDI, ESP32, USB SERIAL

### Step 2 — Background serial thread (`_serial.py:SerialReader._run`)
Opens the port at 921600 baud in a daemon thread. Each loop:
```
data = ser.read(ser.in_waiting or 1)
buf += data
frames, buf = _humi.parse_stream(buf)
for frame in frames: queue.put_nowait(frame)
```
`queue.Queue(maxsize=2000)` — frames dropped when full. Buffer overflow guard: if `len(buf) > 8192`, trim to last 4096 bytes.

### Step 3 — HUMI binary parser (`_humi.py:parse_stream`)
```
[0x01, 0x02, side, group, node_id, seq:u16, payload_len:u16]  ← 9-byte header
[n_sensors:u8] + sensor records                                ← payload
```
- `0x10` ANGLES: `[sens_id, n_samples, t0_us:u64, dt_us:u16, n×i16 centidegrees]`
- `0x11` IMU6:   `[sens_id, n_samples, t0_us:u64, dt_us:u16×3, n×6×i16]` (parser reads only first dt_us, 14-byte header, last 4 bytes skipped)
- `0x12` TOUCH6: `[sens_id, n_samples=1, t0_us:u64, 6×u16 ADC counts]`

`sens_id` byte: upper nibble = finger_idx, lower nibble = com_line. Angles stored as centidegrees → divide by 100.0. Number of angles per node: always 5 for hand group; arm group varies (see `_N_ANGLES_TABLE`).

### Steps 4–5 — Dict → dataclass → yield
`_stream.py:_parse_frame` converts raw dicts to typed dataclasses, adds `ts` via `time.time()`. `GloveStream._iter_serial` calls `queue.get(timeout=1.0)` and yields `GloveFrame` to the client.

---

## digity.viz architecture

The dashboard is a **Flask + Flask-SocketIO** app that auto-starts when `digity-viz` is run. It is always mounted at path prefix `/chiros` (via `DispatcherMiddleware`), so the URL is always `http://127.0.0.1:5001/chiros/`.

**Threading model:**
- `_stream_glove(port)` runs in a daemon thread — feeds frames from `GloveStream` into SocketIO events (`hand_frame`) and optionally into `GlovePublisher` and the recording file.
- Flask-SocketIO runs in a separate daemon thread with `async_mode="threading"`.
- Desktop window (pywebview) runs in the main thread; if pywebview is unavailable, falls back to opening the system browser.

**Persistent state** lives in `~/.digity/`:
- `viz.db` — SQLite: users table, agent_tokens table (auto-creates a local user on first run)
- `viz.key` — Flask secret key (auto-generated)
- `config.json` — station name, serial port, baud rate, recordings directory
- `tasks.json` — list of task names for the recording UI

**Recording format** — each session is a directory under `~/digity-recordings/<session_id>/`:
- `meta.json` — subject, task, hand, station, timestamps, frame count
- `recording.jsonl` — one JSON object per line: `{"ts": float, "side": ..., "sensors": [...]}`

**Agent relay** — `_agent.py` connects to a remote server via Socket.IO `/agent` namespace, streams frames as JSON. The server-side counterpart is in `_server.py` (`/agent` namespace handlers) which re-emits frames to the browser room.

**Authentication** — locally the server auto-logs in the first user; no password prompt. The agent relay authenticates via token (stored in `agent_tokens` table, obtainable from the Setup page).

**Multiview page** (`/chiros/multiview`) — side-by-side view of up to 200 hand model instances. Supports a `?model=<name>&copies=<n>` query string. Available models: `ultraleap`, `shadow`, `allegro`, `inspire`, `ability`, `schunk`.

**3D hand builder JS pattern** — each `static/js/<name>_hand.js` exports one async function:
```js
async function buildXxxHand(loader, isRight) → { root, setJoint, dispose }
// root: THREE.Object3D to add to scene
// setJoint(name, radians): animate a named joint
// dispose(): free GPU resources
```
All hand builders load per-link GLB files from `static/models/<name>_hand/`. To add a new hand, follow this same pattern and add a corresponding model directory.

---

## HUMI protocol constants (for reference)

```python
PKT_TYPE_DATA    = 0x01
PROTOCOL_VERSION = 0x02
SENS_ANGLES      = 0x10
SENS_IMU6        = 0x11
SENS_TOUCH6      = 0x12
GROUP_ARM        = 0
GROUP_HAND       = 1
```

---

## Key decisions — do not revert these

- **Dataclasses instead of raw dicts**: clients get IDE autocomplete and type checking.
- **Background thread for serial reading**: keeps the read buffer from overflowing while the client processes frames.
- **`queue.Queue` between thread and main**: only safe way to pass data across threads in Python.
- **`daemon=True` on all background threads**: threads die automatically when main program exits.
- **`pyzmq` in core dependencies** even though ZMQ mode is optional: it's small and the ZMQ path is valuable for remote-glove setups.
- **`_` prefix on internal modules**: signals to clients and IDEs that internals are not public API.
- **viz always mounted at `/chiros`**: the 3D frontend JS and templates hardcode this prefix; do not change it without updating all templates and static JS.
- **`digity[viz]` as optional extras**: keeps the core SDK dependency-light (pyserial + pyzmq only); rendering deps (Flask, pywebview) are opt-in.
