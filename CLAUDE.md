# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Business context

Digity sells a sensorized exohand (glove with embedded sensors).
Clients receive the hardware and need software to collect the sensor data in their own Python programs.
This SDK is the product they install: `pip install digity`.

There are two planned products:
1. **digity SDK** (this repo) — Python library to collect raw sensor data
2. **digity visualizer** (future, separate repo) — real-time 3D hand rendering, like a lite version of glove-core but only for interpreting data

The SDK must work standalone — no other Digity software required on the client machine.

---

## Development commands

```bash
# Install in editable mode (changes take effect immediately)
pip install -e .

# Run the live example (glove must be plugged in)
python examples/basic.py
python examples/basic.py /dev/ttyUSB0   # explicit port, Linux
python examples/basic.py COM3           # explicit port, Windows

# Build a distribution package
pip install build twine
python -m build                         # creates dist/digity-*.tar.gz and .whl
twine upload dist/*                     # publish to PyPI
```

No automated tests or linter configuration exist yet.

---

## What this repo is NOT

- Not a server, not a dashboard, not a recording tool
- Not dependent on `/home/digity/glove-core` (that is the internal backend, clients don't have it)
- Not responsible for driving hardware — only reading from it

---

## How it fits into the full system

```
[ESP32 glove firmware]
        │  USB cable (serial, 921600 baud, HUMI binary protocol)
        ▼
[Client machine]
  digity SDK (_serial.py reads bytes → _humi.py decodes → GloveFrame objects)
        │
        ▼
  client's Python code  (data collection, research, robotics, etc.)
```

Optional advanced mode: if the glove is on a **remote machine** running glove-core,
the client can use `GloveStream(host="192.168.1.10")` to receive frames over ZMQ instead.
In that case `_serial.py` and `_humi.py` are bypassed.

---

## Package structure

```
digity-sdk/
├── pyproject.toml              — PyPI metadata, name="digity", deps: pyserial, pyzmq
├── CLAUDE.md                   — this file
├── src/
│   └── digity/
│       ├── __init__.py         — public API (re-exports everything clients need)
│       ├── _types.py           — dataclasses: GloveFrame, AnglesSensor, ImuSensor, TouchSensor
│       ├── _humi.py            — HUMI binary protocol parser (ESP32 → Python dicts)
│       ├── _serial.py          — SerialReader thread + find_glove_port() auto-detection
│       └── _stream.py          — GloveStream class (serial/ZMQ modes, dict→dataclass)
└── examples/
    └── basic.py                — plug in glove, run this, see live data
```

Files prefixed with `_` are internal. Clients import only from `digity` (i.e. `__init__.py`).

---

## Public API

```python
from digity import GloveStream, AnglesSensor, ImuSensor, TouchSensor, GloveNotFoundError, Sensor

# Serial mode — glove plugged into this machine (default)
with GloveStream() as stream:              # auto-detects USB port
    for frame in stream:                   # blocks until next frame (~50 Hz)
        print(frame.side, frame.node_id)
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                print(sensor.finger, sensor.samples[-1].angles_deg)

# Explicit port
GloveStream(port="/dev/ttyUSB0")   # Linux
GloveStream(port="COM3")           # Windows

# ZMQ mode — glove on remote machine running glove-core
GloveStream(host="192.168.1.10")
```

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

Sensor types and their key fields:

| Class | Fields |
|---|---|
| `AnglesSensor` | `finger` (int), `com` (int), `samples: list[AnglesSample]` |
| `AnglesSample` | `ts_us` (int, µs), `angles_deg` (list of floats) |
| `ImuSensor` | `finger`, `com`, `samples: list[ImuSample]` |
| `ImuSample` | `ts_us`, `acc: tuple[int,int,int]` (raw i16), `gyro: tuple[int,int,int]` (raw i16) |
| `TouchSensor` | `finger`, `com`, `ts_us`, `channels` (6 floats 0..1), `channels_raw` (6 ints 0..4095) |

`Sensor = Union[AnglesSensor, ImuSensor, TouchSensor]` is exported for use in type annotations.

Always use `isinstance(sensor, AnglesSensor)` to branch — do not compare string type names.

---

## How the code works (internal flow)

### Step 1 — Auto-detect USB port (`_serial.py:find_glove_port`)
Scans `serial.tools.list_ports` for known USB-serial chips:
- VIDs: `1A86` (CH340/CH341), `10C4` (CP210x), `0403` (FTDI), `303A` (ESP32 built-in)
- Keywords in description: CH340, CH341, CP210, FTDI, ESP32, USB SERIAL
Returns the first match (e.g. `/dev/ttyUSB0` on Linux, `COM3` on Windows), or `None`.

### Step 2 — Background serial thread (`_serial.py:SerialReader._run`)
Opens the port at 921600 baud in a daemon thread. Each loop:
```
data = ser.read(ser.in_waiting or 1)
buf += data
frames, buf = _humi.parse_stream(buf)   # parse complete packets, keep leftover
for frame in frames: queue.put_nowait(frame)
```
`queue.Queue(maxsize=2000)` is thread-safe. If the queue is full, new frames are dropped
(keeps stream live rather than accumulating memory).
Buffer overflow guard: if `len(buf) > 8192`, trim to last 4096 bytes (lost sync recovery).

### Step 3 — HUMI binary parser (`_humi.py:parse_stream`)
HUMI packet layout (little-endian):
```
[0x01, 0x02, side, group, node_id, seq:u16, payload_len:u16]  ← 9-byte header
[n_sensors:u8] + sensor records                                ← payload
```
Scanner looks for `0x01 0x02` start bytes, reads `payload_len`, checks if full packet
is in buffer. If not, stops and returns leftover — waits for more serial bytes.

Sensor record types inside the payload:
- `0x10` ANGLES: `[sens_id, n_samples, t0_us:u64, dt_us:u16, n×i16 centidegrees]`
- `0x11` IMU6:   `[sens_id, n_samples, t0_us:u64, dt_us:u16×3, n×6×i16]`  ← parser reads only the first dt_us (14-byte header, last 4 bytes skipped)
- `0x12` TOUCH6: `[sens_id, n_samples=1, t0_us:u64, 6×u16 ADC counts]`

`sens_id` byte: upper nibble = finger_idx, lower nibble = com_line.
Angles stored as centidegrees (i16) → divide by 100.0 for degrees.
Number of angles per node: always 5 for hand group; arm group varies by node (see `_N_ANGLES_TABLE`).

### Step 4 — Dict → dataclass conversion (`_stream.py:_parse_frame`)
Converts the raw dicts from `_humi.py` into typed dataclass instances from `_types.py`.
Adds `ts` (host timestamp via `time.time()`).

### Step 5 — Yielding to the client (`_stream.py:GloveStream._iter_serial`)
Generator loop — calls `queue.get(timeout=1.0)`, converts each dict to `GloveFrame`,
yields it to the client. If background thread sets `_error`, raises it in the main thread.

### Context manager
`__enter__` → `connect()` → starts serial thread.
`__exit__` → `disconnect()` → sets `_running=False` → thread exits, serial port closed.
Guarantees cleanup even if client code crashes inside the `with` block.

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

## Releasing to PyPI

Before first publish: verify `pypi.org/project/digity` is free.
If the name is taken, change `name` in `pyproject.toml` (e.g. `digity-glove` or `digity-sdk`).
The import stays `from digity import ...` regardless — it is controlled by the folder name `src/digity/`.

When releasing a new version: bump `version` in **both** `pyproject.toml` and `src/digity/__init__.py`.

---

## Key decisions — do not revert these

- **Dataclasses instead of raw dicts**: clients get IDE autocomplete and type checking. Returning plain dicts would be worse UX.
- **Background thread for serial reading**: keeps the read buffer from overflowing while the client processes frames.
- **`queue.Queue` between thread and main**: only safe way to pass data across threads in Python.
- **`daemon=True` on the thread**: thread dies automatically when main program exits — no zombie threads.
- **`pyzmq` kept as a dependency** even though ZMQ mode is optional: it's small and the ZMQ path is valuable for remote-glove setups and for future visualizer integration.
- **`_` prefix on internal modules**: signals to clients (and IDEs) that `_humi`, `_serial`, `_stream`, `_types` are not part of the public API.

---

## Future: visualizer

A future `digity-viz` package will import `GloveStream` from this SDK and render a real-time 3D hand.
Keep this SDK dependency-light (pyserial + pyzmq only).
All rendering dependencies (Three.js wrapper, PyQt, etc.) belong in the visualizer package, not here.
