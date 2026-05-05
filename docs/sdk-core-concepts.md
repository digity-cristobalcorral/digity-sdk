---
eyebrow: SDK
lede: Three ideas that explain everything else — the stream context manager, the frame structure, and how sensors map to finger indices.
---

## GloveStream — the entry point

`GloveStream` is a Python context manager that opens the glove connection and yields `GloveFrame` objects. It supports two transport modes:

| Mode | How to activate | Use case |
|---|---|---|
| Serial (auto) | `GloveStream()` | Glove plugged into this machine — port detected automatically. |
| Serial (explicit) | `GloveStream(port="/dev/ttyUSB0")` | Multiple USB devices attached — pick the right one. |
| ZMQ remote | `GloveStream(host="192.168.1.10")` | Glove is on another machine running `GlovePublisher`. |

```python
from digity import GloveStream

# auto-detect USB port
with GloveStream() as stream:
    for frame in stream:
        ...

# receive from a remote machine
with GloveStream(host="192.168.1.10") as stream:
    for frame in stream:
        ...
```

## GloveFrame — one packet from the glove

Each iteration yields a `GloveFrame`. It corresponds to one HUMI protocol packet from the ESP32 firmware.

| Field | Type | Description |
|---|---|---|
| `ts` | `float` | Host timestamp (seconds since epoch, set on receive). |
| `side` | `"right" \| "left"` | Which hand the packet came from. |
| `group` | `"hand" \| "arm"` | Sensor group: finger nodes or forearm/wrist nodes. |
| `node_id` | `int` | PCB node number within the glove (0–4). |
| `seq` | `int` | Packet sequence counter (0–65535, wraps around). |
| `sensors` | `list[Sensor]` | Sensor objects in this packet. |

## Sensor types and finger index

Always dispatch with `isinstance` — never compare string names.

```python
from digity import GloveStream, AnglesSensor, ImuSensor, TouchSensor

with GloveStream() as stream:
    for frame in stream:
        if frame.group != "hand":
            continue  # skip arm/wrist sensors

        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                angles = sensor.samples[-1].angles_deg
                print(f"finger {sensor.finger}: {angles}")

            elif isinstance(sensor, TouchSensor):
                print(f"touch {sensor.finger}: {sensor.channels}")

            elif isinstance(sensor, ImuSensor):
                last = sensor.samples[-1]
                print(f"imu {sensor.finger}: acc={last.acc}")
```

The `finger` attribute maps to anatomy:

| finger index | Digit | Angle channels (group=hand) |
|---|---|---|
| `0` | Thumb | 5 channels |
| `1` | Index | 5 channels |
| `2` | Middle | 5 channels |
| `3` | Ring | 5 channels |
| `4` | Pinky | 5 channels |

!!! warning
    Arm-group packets (`frame.group == "arm"`) have 2–3 angle channels and `finger=0` in their `sens_id`, which looks like thumb data. **Always filter by `frame.group == "hand"`** before routing finger angles.

## Samples — sub-frame timing

Each sensor object carries a `samples` list. The firmware may batch multiple samples into one packet. Use `samples[-1]` for the latest reading; iterate over all `samples` for full-rate processing.

| Sample type | Fields |
|---|---|
| `AnglesSample` | `ts_us` (µs timestamp), `angles_deg` (list of floats in degrees) |
| `ImuSample` | `ts_us`, `acc` (tuple of 3 raw i16), `gyro` (tuple of 3 raw i16) |
| `TouchSensor` | No sample list — the sensor is the sample. `ts_us`, `channels` (6 floats 0–1), `channels_raw` (6 ints 0–4095). |

## GlovePublisher — broadcast over ZMQ

Fan out glove data to multiple processes or machines:

```python
from digity import GlovePublisher, GloveStream

# Option A: alongside custom processing
with GlovePublisher() as pub:
    with GloveStream() as stream:
        for frame in stream:
            pub.publish(frame)
            process(frame)   # your code here

# Option B: standalone publisher (blocks, Ctrl-C to stop)
with GlovePublisher() as pub:
    pub.run()
```

## Where to go next

- [API reference](sdk-api-reference.md) — all classes and their fields.
- [ROS2 bridge](integrations-ros2.md) — how GloveStream feeds into ROS2 topics.
- [Dashboard](integrations-dashboard.md) — the built-in recording and visualization tool.
