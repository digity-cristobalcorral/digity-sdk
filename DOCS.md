# digity SDK — Developer Documentation

> Version 0.2.1 · Python ≥ 3.9 · Proprietary

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [Core API Reference](#4-core-api-reference)
   - [GloveStream](#glovestream)
   - [GloveFrame](#gloveframe)
   - [AnglesSensor / AnglesSample](#anglessensor--anglessample)
   - [ImuSensor / ImuSample](#imusensor--imusample)
   - [TouchSensor](#touchsensor)
   - [GlovePublisher](#glovepublisher)
   - [GloveNotFoundError](#glovenotfounderror)
5. [Dashboard (digity\[viz\])](#5-dashboard-digityviz)
6. [Agent Mode (digity\[agent\])](#6-agent-mode-digityagent)
7. [Remote Streaming (ZMQ)](#7-remote-streaming-zmq)
8. [Recording Format](#8-recording-format)
9. [Configuration](#9-configuration)
10. [CLI Reference](#10-cli-reference)
11. [REST API Reference](#11-rest-api-reference)
12. [WebSocket Events](#12-websocket-events)
13. [Common Patterns](#13-common-patterns)

---

## 1. Overview

The **digity SDK** provides Python access to the Digity sensorized exohand — a glove that captures real-time hand motion data including joint angles, 6-axis IMU, and capacitive touch. The SDK handles the USB serial connection, binary protocol decoding, and threading so you get clean typed Python objects at approximately 50 Hz.

Three install targets are available:

| Target | What it includes |
|--------|-----------------|
| `pip install digity` | Core SDK only — stream sensor data in Python |
| `pip install "digity[viz]"` | Core SDK + local real-time dashboard |
| `pip install "digity[agent]"` | Core SDK + agent relay to cloud dashboard |

---

## 2. Installation

```bash
# Core SDK (sensor streaming only)
pip install digity

# Full local dashboard
pip install "digity[viz]"

# Agent mode (relay to cloud dashboard)
pip install "digity[agent]"
```

**Requirements:** Python 3.9 or later, Digity exohand connected via USB.

---

## 3. Quick Start

```python
from digity import GloveStream, AnglesSensor, ImuSensor, TouchSensor

with GloveStream() as stream:
    for frame in stream:
        print(f"side={frame.side}  node={frame.node_id}  seq={frame.seq}")

        for sensor in frame.sensors:

            if isinstance(sensor, AnglesSensor):
                angles = sensor.samples[-1].angles_deg
                print(f"  finger {sensor.finger} angles: {angles}")

            elif isinstance(sensor, ImuSensor):
                s = sensor.samples[-1]
                print(f"  finger {sensor.finger} acc={s.acc}  gyro={s.gyro}")

            elif isinstance(sensor, TouchSensor):
                print(f"  finger {sensor.finger} touch={sensor.channels}")
```

The `with` block handles connection and cleanup automatically. Press **Ctrl+C** to stop.

---

## 4. Core API Reference

### GloveStream

`digity.GloveStream` — main entry point for receiving live sensor data.

```python
class GloveStream:
    def __init__(
        self,
        port: Optional[str] = None,
        baud: int = 921600,
        *,
        host: Optional[str] = None,
        zmq_port: int = 5555,
    ) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `port` | `str \| None` | `None` | Serial port (e.g. `"COM3"`, `"/dev/ttyUSB0"`). `None` = auto-detect. |
| `baud` | `int` | `921600` | Baud rate for serial connection. |
| `host` | `str \| None` | `None` | Remote host IP for ZMQ mode. If set, serial is not used. |
| `zmq_port` | `int` | `5555` | ZMQ port when using `host`. |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `connect()` | `GloveStream` | Open the connection. Called automatically by `__enter__`. |
| `disconnect()` | `None` | Close the connection. Called automatically by `__exit__`. |
| `__enter__()` | `GloveStream` | Context manager entry. |
| `__exit__(*_)` | `None` | Context manager exit — always calls `disconnect()`. |
| `__iter__()` | `Iterator[GloveFrame]` | Yields frames. Blocks until next frame arrives (1 s timeout). |

**Exceptions:**

- `GloveNotFoundError` — raised at connect time if the glove port cannot be found (serial mode only).
- `RuntimeError` — raised if iterating before connecting.
- `ImportError` — raised if ZMQ mode is requested but `pyzmq` is not installed.

**Examples:**

```python
# Auto-detect serial port
with GloveStream() as stream:
    for frame in stream:
        ...

# Explicit serial port
with GloveStream(port="COM3") as stream:
    for frame in stream:
        ...

# ZMQ remote mode
with GloveStream(host="192.168.1.10") as stream:
    for frame in stream:
        ...

# Manual connect / disconnect (for thread-based control)
stream = GloveStream()
stream.connect()
for frame in stream:
    ...
stream.disconnect()
```

---

### GloveFrame

Every iteration of `GloveStream` yields one `GloveFrame`.

```python
@dataclass
class GloveFrame:
    ts:       float        # Host timestamp (seconds since epoch) when frame arrived
    side:     str          # "right" or "left"
    group:    str          # "hand" or "arm"
    node_id:  int          # PCB node number on the glove
    seq:      int          # Packet counter 0–65535, wraps around
    sensors:  list[Sensor] # AnglesSensor, ImuSensor, or TouchSensor objects
```

`Sensor` is a type alias: `Union[AnglesSensor, ImuSensor, TouchSensor]`.

---

### AnglesSensor / AnglesSample

Joint angle readings for one finger node.

```python
@dataclass
class AnglesSensor:
    finger:  int                  # Finger index (0=thumb … 4=pinky)
    com:     int                  # Communication line index
    samples: list[AnglesSample]   # One or more timestamped readings

@dataclass
class AnglesSample:
    ts_us:      int          # Sensor timestamp in microseconds
    angles_deg: list[float]  # Joint angles in degrees (5 values for hand group)
```

**Usage:**

```python
if isinstance(sensor, AnglesSensor):
    latest = sensor.samples[-1]
    print(latest.angles_deg)   # e.g. [12.3, 45.1, 30.0, 5.5, 2.0]
```

**Finger index mapping:**

| Index | Finger |
|-------|--------|
| 0 | Thumb |
| 1 | Index |
| 2 | Middle |
| 3 | Ring |
| 4 | Pinky |

---

### ImuSensor / ImuSample

6-axis IMU (accelerometer + gyroscope) for one finger node.

```python
@dataclass
class ImuSensor:
    finger:  int               # Finger index
    com:     int               # Communication line index
    samples: list[ImuSample]   # One or more timestamped readings

@dataclass
class ImuSample:
    ts_us: int                      # Sensor timestamp in microseconds
    acc:   tuple[int, int, int]     # Accelerometer x/y/z — raw i16 counts
    gyro:  tuple[int, int, int]     # Gyroscope x/y/z — raw i16 counts
```

**Usage:**

```python
if isinstance(sensor, ImuSensor):
    s = sensor.samples[-1]
    print(s.acc)    # e.g. (312, -128, 16384)
    print(s.gyro)   # e.g. (5, -12, 3)
```

---

### TouchSensor

6-channel capacitive touch for one finger node.

```python
@dataclass
class TouchSensor:
    finger:       int         # Finger index
    com:          int         # Communication line index
    ts_us:        int         # Sensor timestamp in microseconds
    channels:     list[float] # 6 values normalised 0.0–1.0
    channels_raw: list[int]   # 6 raw ADC counts 0–4095
```

**Usage:**

```python
if isinstance(sensor, TouchSensor):
    print(sensor.channels)      # [0.0, 0.82, 0.0, 0.0, 0.41, 0.0]
    print(sensor.channels_raw)  # [0, 3358, 0, 0, 1680, 0]
```

---

### GlovePublisher

Broadcasts `GloveFrame` objects over a ZMQ PUB socket so multiple remote subscribers can receive the same data stream.

```python
class GlovePublisher:
    def __init__(
        self,
        zmq_port: int = 5555,
        bind: str = "tcp://*",
    ) -> None
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `zmq_port` | `5555` | Port to bind. |
| `bind` | `"tcp://*"` | Bind address. |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `start()` | `GlovePublisher` | Open ZMQ PUB socket. Returns self for chaining. |
| `stop()` | `None` | Close ZMQ socket. |
| `publish(frame)` | `None` | Publish one frame. Non-blocking; silently dropped if socket is closed. Thread-safe. |
| `run(port, baud)` | `None` | Read from serial and publish until Ctrl+C. Blocks the calling thread. |
| `__enter__()` | `GlovePublisher` | Context manager entry. |
| `__exit__(*_)` | `None` | Context manager exit. |

**ZMQ wire format:**

- Topic: `b"sensor"`
- Payload: JSON `{"type": "sensor_frame", "ts": <float>, "frame": {...}}`

**Examples:**

```python
# Standalone publisher (blocks until Ctrl+C)
with GlovePublisher() as pub:
    pub.run()

# Embedded in custom loop
with GlovePublisher() as pub:
    with GloveStream() as stream:
        for frame in stream:
            pub.publish(frame)
            # ... your processing here
```

---

### GloveNotFoundError

```python
class GloveNotFoundError(RuntimeError): ...
```

Raised by `GloveStream.connect()` and `GlovePublisher.run()` when the glove USB port cannot be found automatically.

```python
from digity import GloveStream, GloveNotFoundError

try:
    with GloveStream() as stream:
        for frame in stream:
            ...
except GloveNotFoundError:
    print("Glove not found — check the USB cable")
```

---

## 5. Dashboard (digity[viz])

`digity[viz]` ships a full web-based dashboard that visualises live sensor data, records sessions, and can relay data from a remote agent.

### Launch

```bash
# Auto-detect glove port — opens as desktop window
digity-viz

# Explicit serial port
digity-viz --port COM3

# Open in browser instead of desktop window
digity-viz --browser
```

Or from Python:

```python
import digity.viz
digity.viz.start()                   # desktop window (default)
digity.viz.start(desktop=False)      # browser
digity.viz.start(port="COM3")        # explicit port
```

The dashboard runs at `http://localhost:5001/chiros/` and opens automatically. No login is required for local use — a default user is created on first run.

### Pages

| URL | Description |
|-----|-------------|
| `/chiros/` | Live viewer — 3-D hand model with real-time joint angles |
| `/chiros/record` | Recording — start/stop sessions, download, delete |
| `/chiros/setup` | Configuration — recordings folder, agent token, SDK info, update check |

### Data directory

All persistent data is stored in `~/.digity/`:

| File | Contents |
|------|----------|
| `viz.db` | SQLite database — users and agent tokens |
| `viz.key` | Flask secret key (auto-generated) |
| `config.json` | Station settings, recordings path, port |
| `tasks.json` | Task labels for recording metadata |

---

## 6. Agent Mode (digity[agent])

Agent mode lets a PC with the glove connected stream data to a remote digity dashboard (cloud or LAN) without any separate `.exe`.

### Install

```bash
pip install "digity[agent]"
```

### Run

```bash
# Using digity-agent CLI
digity-agent --token YOUR_TOKEN

# Using digity-viz with --agent flag
digity-viz --agent --token YOUR_TOKEN

# Custom server URL or explicit port
digity-agent --token YOUR_TOKEN --url https://your-server/chiros
digity-agent --token YOUR_TOKEN --port COM3
```

Or from Python:

```python
from digity.viz._agent import run as agent_run

agent_run(token="YOUR_TOKEN")
agent_run(token="YOUR_TOKEN", url="https://your-server/chiros", port="COM3")
```

### How it works

1. The agent connects to the server's Socket.IO `/agent` namespace and authenticates with the token.
2. For every `GloveFrame` received from the glove, the agent emits a `frame` event to the server.
3. The server relays the frame to all browser clients logged in with the matching account.
4. If the connection drops (glove or server), the agent automatically retries every 5 seconds.

### Getting a token

Copy your personal token from the **Setup** page of the dashboard:
- Local: `http://localhost:5001/chiros/setup`
- Cloud: `https://app.digity.de/chiros/setup`

---

## 7. Remote Streaming (ZMQ)

If the glove is connected to a **server machine** that runs `GlovePublisher`, client machines can receive frames over the network without any USB connection.

### Server (machine with glove)

```python
from digity import GlovePublisher

with GlovePublisher(zmq_port=5555) as pub:
    pub.run()   # blocks; auto-detects glove
```

Or via CLI (if the dashboard is running):

```bash
digity-viz --port COM3   # the dashboard publishes automatically
```

### Client (any machine on the network)

```python
from digity import GloveStream

with GloveStream(host="192.168.1.10") as stream:         # default port 5555
    for frame in stream:
        print(frame.side, frame.sensors)

# Custom ZMQ port
with GloveStream(host="192.168.1.10", zmq_port=5556) as stream:
    ...
```

---

## 8. Recording Format

Sessions are saved as directories under the configured `recordings_dir` (default `~/digity-recordings`):

```
recordings_dir/
└── <username>/
    └── <session_id>/
        ├── meta.json        ← session metadata
        └── recording.jsonl  ← sensor frames, one JSON object per line
```

### Session ID format

```
{subject}_{task}_{YYYY-MM-DDTHH-MM-SS}
```

Example: `user01_grasp_2025-04-22T10-30-00`

### meta.json

```json
{
  "session_id":    "user01_grasp_2025-04-22T10-30-00",
  "user_id":       "user01",
  "task":          "grasp",
  "hand":          "right",
  "station":       "Station 1",
  "notes":         "",
  "host_ts_start": 1745311800.123,
  "recorded_by":   "admin",
  "host_ts_end":   1745311815.456,
  "duration_s":    15.333,
  "frame_count":   766,
  "bytes_written": 204800
}
```

### recording.jsonl

Each line is a JSON object representing one `GloveFrame`:

```json
{"ts": 1745311800.200, "side": "right", "group": "hand", "node_id": 1, "seq": 1042, "sensors": [...]}
```

### Read a recording in Python

```python
import json

with open("session_dir/recording.jsonl") as f:
    for line in f:
        frame = json.loads(line)
        print(frame["ts"], frame["side"])
```

---

## 9. Configuration

The dashboard reads and writes `~/.digity/config.json`. Settings are applied immediately — no restart required.

### Default configuration

```json
{
  "station_name":   "Station 1",
  "serial_port":    "",
  "baud_rate":      921600,
  "recordings_dir": "~/digity-recordings"
}
```

### Fields

| Key | Type | Description |
|-----|------|-------------|
| `station_name` | `str` | Station label shown in recording metadata. |
| `serial_port` | `str` | Override auto-detection with an explicit port (`""` = auto). |
| `baud_rate` | `int` | Serial baud rate — do not change unless instructed. |
| `recordings_dir` | `str` | Absolute path where session directories are created. |

### Change via the Setup page

Go to **Setup → Recordings Folder**, enter the new path, and click **Save**. The next recording will use the new location.

### Change via API

```bash
curl -X POST http://localhost:5001/chiros/api/config \
  -H "Content-Type: application/json" \
  -d '{"recordings_dir": "D:/recordings"}'
```

---

## 10. CLI Reference

### digity-viz

```
digity-viz [OPTIONS]

Options:
  --port PORT     Serial port (e.g. COM3, /dev/ttyUSB0). Default: auto-detect.
  --browser       Open dashboard in system browser instead of desktop window.
  --agent         Run in agent mode — stream glove to a remote dashboard.
                  Requires --token.
  --token TOKEN   Agent token from the Setup page.
  --url URL       Remote server URL. Default: https://app.digity.de/chiros
```

### digity-agent

```
digity-agent [OPTIONS]

Options:
  --token TOKEN   (required) Agent token from the Setup page.
  --url URL       Remote server URL. Default: https://app.digity.de/chiros
  --port PORT     Serial port. Default: auto-detect.
```

If `digity-viz` or `digity-agent` is not on PATH (Windows Store Python), use:

```bash
python -m digity.viz [OPTIONS]
python -m digity.viz --agent --token YOUR_TOKEN [OPTIONS]
```

---

## 11. REST API Reference

All endpoints are under the `APP_PREFIX` (`/chiros` by default) and require an active session (login). For local use the default user is automatically authenticated.

### Recording

| Method | Path | Body | Response |
|--------|------|------|----------|
| `POST` | `/api/record/start` | `{user_id?, task?, hand?, notes?}` | `{ok, session_id}` |
| `POST` | `/api/record/stop` | — | `{ok, session_id, frame_count}` |
| `GET` | `/api/record/status` | — | `{recording, session_id, frame_count, duration}` |

### Sessions

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/api/sessions` | `[{name, meta, size_bytes, mtime}, …]` |
| `GET` | `/api/sessions/<name>/download` | `recording.jsonl` file download |
| `DELETE` | `/api/sessions/<name>` | `{ok}` |

### Tasks

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/api/tasks` | — | `["grasp", "pinch", …]` |
| `POST` | `/api/tasks` | `{name}` | `{ok}` |
| `DELETE` | `/api/tasks/<name>` | — | `{ok}` |

### Configuration

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/api/config` | — | `{station_name, serial_port, baud_rate, recordings_dir}` |
| `POST` | `/api/config` | `{key: value, …}` | `{ok}` |

### Agent Token

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/api/agent/token` | `{token}` |
| `POST` | `/api/agent/token/regenerate` | `{token}` |

### Status & Updates

| Method | Path | Response |
|--------|------|----------|
| `GET` | `/api/status` | `{glove_connected, glove_port, glove_hz, recording, session_id, sdk_version, python_version}` |
| `GET` | `/api/check-update` | `{current, latest, has_update}` or `{current, error}` |

---

## 12. WebSocket Events

The dashboard uses Socket.IO. Connect with:

```javascript
const socket = io({ path: '/chiros/socket.io' });
```

### Events emitted by the server (listen on the client)

| Event | Payload | Description |
|-------|---------|-------------|
| `glove_telemetry` | `{connected, port, hz?, recording?, frame_count?, session_id?, duration?, error?}` | Glove connection status, updated continuously. |
| `hand_frame` | sensor frame dict | One decoded sensor frame — same structure as `recording.jsonl` lines. |
| `recording_state` | `{recording, session_id, meta?, frame_count?}` | Emitted when a recording starts or stops. |

### Agent namespace (`/agent`)

Agents connect to `namespace="/agent"` and authenticate via the `auth` object:

```python
sio.connect(url, auth={"token": TOKEN}, namespaces=["/agent"])
```

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | server → agent | Server validates token; returns `False` if invalid. |
| `frame` | agent → server | Emit one sensor frame dict; server relays it to the browser. |
| `disconnect` | server → agent | Agent disconnected. |

---

## 13. Common Patterns

### Record data to CSV

```python
import csv
from digity import GloveStream, AnglesSensor

with GloveStream() as stream, open("recording.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["ts", "finger", "a0", "a1", "a2", "a3", "a4"])
    for frame in stream:
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                a = sensor.samples[-1].angles_deg
                writer.writerow([frame.ts, sensor.finger] + a)
```

### Detect a closed fist

```python
from digity import GloveStream, AnglesSensor

with GloveStream() as stream:
    finger_angles = {}
    for frame in stream:
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                finger_angles[sensor.finger] = sensor.samples[-1].angles_deg

        if len(finger_angles) == 5:
            avg_flex = sum(finger_angles[f][1] for f in range(1, 5)) / 4
            if avg_flex > 60:
                print("Fist detected!")
```

### Stop the stream from another thread

```python
import threading
from digity import GloveStream

stream = GloveStream()
stream.connect()

def stop_after(seconds):
    import time; time.sleep(seconds)
    stream.disconnect()

threading.Thread(target=stop_after, args=(10,), daemon=True).start()

for frame in stream:
    print(frame.seq)
```

### Type annotation helper

```python
from digity import Sensor, AnglesSensor, ImuSensor, TouchSensor

def process(sensor: Sensor) -> None:
    if isinstance(sensor, AnglesSensor):
        ...
    elif isinstance(sensor, ImuSensor):
        ...
    elif isinstance(sensor, TouchSensor):
        ...
```

### Read a saved recording

```python
import json
from pathlib import Path

session_dir = Path("~/digity-recordings/admin/user01_grasp_2025-04-22T10-30-00").expanduser()
meta = json.loads((session_dir / "meta.json").read_text())
print(f"Duration: {meta['duration_s']:.1f}s  Frames: {meta['frame_count']}")

with open(session_dir / "recording.jsonl") as f:
    for line in f:
        frame = json.loads(line)
        # frame["sensors"] is a list of dicts with keys: type, finger, com, samples / channels
```

### Update the package

```bash
pip install --upgrade digity
pip install --upgrade "digity[viz]"
pip install --upgrade "digity[agent]"
```

---

*© Digity. All rights reserved.*
