# digity SDK

> Python SDK for the **Digity sensorized exohand** — plug in the glove, stream live sensor data in three lines.

The Digity exohand is a sensorized glove that captures real-time hand motion data: joint angles for every finger, 6-axis IMU (accelerometer + gyroscope), and 6-channel capacitive touch per node. This SDK handles the USB connection, binary protocol decoding, and threading — so you get clean, typed Python objects at ~50 Hz without any low-level plumbing.

```python
from digity import GloveStream, AnglesSensor

with GloveStream() as stream:
    for frame in stream:
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                print(sensor.finger, sensor.samples[-1].angles_deg)
```

**Use cases:** motion capture, rehabilitation, robotics control, gesture recognition, HCI research, data collection.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [GloveStream](#glovestream)
- [Data types](#data-types)
- [Common patterns](#common-patterns)
- [Error handling](#error-handling)
- [Real-time dashboard](#real-time-dashboard-digityviz)
- [Agent mode — stream to cloud](#agent-mode-digityagent)
- [Publish over the network (ZMQ)](#publish-over-the-network-zmq)
- [Remote ZMQ receive](#remote-zmq-receive)
- [Connection speed](#connection-speed)

---

## Installation

```bash
# Core SDK — sensor data in Python only
pip install digity

# SDK + real-time local dashboard
pip install "digity[viz]"

# SDK + cloud agent relay
pip install "digity[agent]"
```

**Requirements:** Python 3.9 or later · Digity exohand connected via USB.

---

## Quick start

Plug in the glove, then run:

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

## GloveStream

```python
GloveStream(
    port=None,       # serial port e.g. "COM3" / "/dev/ttyUSB0" — None = auto-detect
    baud=921600,     # baud rate
    *,
    host=None,       # remote host IP for ZMQ mode
    zmq_port=5555,   # ZMQ port when using host
)
```

| Method | Description |
|--------|-------------|
| `connect()` | Open the connection. Called automatically by `with`. |
| `disconnect()` | Close the connection. Called automatically on `with` exit. |
| `__iter__()` | Yields `GloveFrame` objects. Blocks until the next frame arrives. |

**Specifying the USB port** — the SDK auto-detects on all platforms. If auto-detection fails:

```python
GloveStream(port="/dev/ttyUSB0")          # Linux
GloveStream(port="/dev/tty.usbserial-0001")  # macOS
GloveStream(port="COM3")                  # Windows
```

**Stop from another thread:**

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

---

## Data types

### `GloveFrame`

Every iteration of `GloveStream` yields one `GloveFrame`:

| Field | Type | Description |
|-------|------|-------------|
| `ts` | `float` | Host timestamp (seconds since epoch) when the frame arrived |
| `side` | `str` | `"right"` or `"left"` |
| `group` | `str` | `"hand"` or `"arm"` |
| `node_id` | `int` | PCB node number on the glove |
| `seq` | `int` | Packet counter 0–65535, wraps around |
| `sensors` | `list[Sensor]` | List of sensor readings in this frame |

`Sensor` is `Union[AnglesSensor, ImuSensor, TouchSensor]`.

---

### `AnglesSensor`

Joint angles for one finger node.

| Field | Type | Description |
|-------|------|-------------|
| `finger` | `int` | Finger index — 0 = thumb, 1 = index, 2 = middle, 3 = ring, 4 = pinky |
| `com` | `int` | Communication line index |
| `samples` | `list[AnglesSample]` | One or more timestamped angle readings |

**`AnglesSample`**

| Field | Type | Description |
|-------|------|-------------|
| `ts_us` | `int` | Sensor timestamp in microseconds |
| `angles_deg` | `list[float]` | Joint angles in degrees (5 values for hand group) |

```python
if isinstance(sensor, AnglesSensor):
    latest = sensor.samples[-1]
    print(latest.angles_deg)   # e.g. [12.3, 45.1, 30.0, 5.5, 2.0]
```

---

### `ImuSensor`

6-axis IMU (accelerometer + gyroscope) for one finger node.

| Field | Type | Description |
|-------|------|-------------|
| `finger` | `int` | Finger index |
| `com` | `int` | Communication line index |
| `samples` | `list[ImuSample]` | One or more timestamped IMU readings |

**`ImuSample`**

| Field | Type | Description |
|-------|------|-------------|
| `ts_us` | `int` | Sensor timestamp in microseconds |
| `acc` | `tuple[int, int, int]` | Accelerometer x/y/z — raw i16 counts |
| `gyro` | `tuple[int, int, int]` | Gyroscope x/y/z — raw i16 counts |

```python
if isinstance(sensor, ImuSensor):
    s = sensor.samples[-1]
    print(s.acc)    # e.g. (312, -128, 16384)
    print(s.gyro)   # e.g. (5, -12, 3)
```

---

### `TouchSensor`

6-channel capacitive touch for one finger node.

| Field | Type | Description |
|-------|------|-------------|
| `finger` | `int` | Finger index |
| `com` | `int` | Communication line index |
| `ts_us` | `int` | Sensor timestamp in microseconds |
| `channels` | `list[float]` | 6 values normalised 0.0–1.0 |
| `channels_raw` | `list[int]` | 6 raw ADC counts 0–4095 |

```python
if isinstance(sensor, TouchSensor):
    print(sensor.channels)      # [0.0, 0.82, 0.0, 0.0, 0.41, 0.0]
    print(sensor.channels_raw)  # [0, 3358, 0, 0, 1680, 0]
```

---

### Type annotation helper

```python
from digity import Sensor  # Union[AnglesSensor, ImuSensor, TouchSensor]

def process(sensor: Sensor) -> None:
    if isinstance(sensor, AnglesSensor):
        ...
```

---

## Common patterns

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
        print(frame["ts"], frame["side"])
```

---

## Error handling

```python
from digity import GloveStream, GloveNotFoundError

try:
    with GloveStream() as stream:
        for frame in stream:
            ...
except GloveNotFoundError:
    print("Glove not found — check the USB cable")
except KeyboardInterrupt:
    pass
```

`GloveNotFoundError` is raised at connection time if the glove port cannot be found.

---

## Real-time dashboard (`digity[viz]`)

`digity[viz]` ships a full local dashboard that visualises live hand data in 3-D, records labelled sessions, and serves as a local relay for remote agents — no internet required.

```bash
pip install "digity[viz]"

digity-viz              # opens as a desktop window
digity-viz --port COM3  # explicit serial port
digity-viz --browser    # open in system browser instead
```

Or from Python:

```python
import digity.viz
digity.viz.start()
```

The dashboard runs at `http://localhost:5001/chiros/` and opens automatically.

**Dashboard pages:**

| Page | Description |
|------|-------------|
| Viewer | Live 3-D hand model with real-time joint angles |
| Record | Start/stop sessions, download `.jsonl` files, manage recordings |
| Setup | Recordings folder, agent token, update checker |

**Session recordings** are saved to `~/digity-recordings/` by default. Each session creates a directory containing `meta.json` (duration, frame count, task label) and `recording.jsonl` (one JSON frame per line at ~50 Hz).

---

## Agent mode (`digity[agent]`)

Stream the glove directly to the cloud dashboard — no separate `agent.exe` needed.

```bash
pip install "digity[agent]"

# copy your token from the dashboard → Setup page
digity-agent --token YOUR_TOKEN

# or via the digity-viz command
digity-viz --agent --token YOUR_TOKEN

# explicit port or custom server URL
digity-agent --token YOUR_TOKEN --port COM3
digity-agent --token YOUR_TOKEN --url https://app.digity.de/chiros
```

The agent auto-detects the glove, connects to the server, and streams frames in real time. It reconnects automatically if either connection drops.

If `digity-agent` is not on PATH (common with Windows Store Python), use:

```bash
python -m digity.viz --agent --token YOUR_TOKEN
```

---

## Publish over the network (ZMQ)

`GlovePublisher` broadcasts frames over a ZMQ PUB socket so multiple processes or machines can subscribe to the same glove.

```python
from digity import GlovePublisher

# Standalone — blocks until Ctrl+C
with GlovePublisher() as pub:
    pub.run()

# Embedded in a custom loop
from digity import GloveStream, GlovePublisher

with GlovePublisher() as pub, GloveStream() as stream:
    for frame in stream:
        pub.publish(frame)
        # ... your processing here
```

```python
GlovePublisher(
    zmq_port=5555,     # port to bind
    bind="tcp://*",    # bind address
)
```

| Method | Description |
|--------|-------------|
| `start()` | Open ZMQ PUB socket. Returns self. |
| `stop()` | Close socket. |
| `publish(frame)` | Publish one frame. Non-blocking, thread-safe. |
| `run(port, baud)` | Read from serial and publish. Blocks until Ctrl+C. |

---

## Remote ZMQ receive

On any machine that can reach the publisher over the network:

```python
from digity import GloveStream

with GloveStream(host="192.168.1.10") as stream:        # default port 5555
    for frame in stream:
        print(frame.side, frame.sensors)

# Custom ZMQ port
with GloveStream(host="192.168.1.10", zmq_port=5556) as stream:
    ...
```

No USB connection is needed on the receiving machine.

---

## Connection speed

The glove streams at approximately **50 Hz**. Each `for frame in stream` call blocks until the next frame arrives (up to 1 second timeout before checking for errors).

The SDK uses a background thread and an internal queue so your processing code never stalls the serial buffer. If your code is slower than 50 Hz, frames are dropped to keep the stream live rather than accumulating memory.

---

## Updating

```bash
pip install --upgrade digity
pip install --upgrade "digity[viz]"    # if using the dashboard
pip install --upgrade "digity[agent]"  # if using agent mode
```

---

## License

© Digity. All rights reserved.
