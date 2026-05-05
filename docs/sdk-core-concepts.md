---
eyebrow: SDK
lede: "Five ideas that explain everything else: device identity, the three streams, the data package, the three sync scopes, and the host clock."
---

# SDK Core Concepts

## 1. Device identity

Every Chiros unit has a serial number and a side (left or right). `Device.discover()` scans connected USB devices and returns a list of `DeviceInfo` objects. `Device.open()` opens a connection; if exactly one device is attached, the serial number is optional.

```python
import chiros

# List all connected devices
devices = chiros.Device.discover()
for d in devices:
    print(d.serial, d.side, d.firmware)

# Open the only connected device
device = chiros.Device.open()

# Open a specific device by serial number
device = chiros.Device.open(serial="00042")
```

## 2. Three streams

Chiros produces three independent data streams. All three are active simultaneously; you choose which ones to consume in your application.

| Stream | Rate | Shape | Purpose |
|---|---|---|---|
| kinematics | 100 Hz | `q[N_dofs]` | Joint angles in radians, full hand |
| touch | 30–100 Hz | `t[N_pads]` | Normalized contact pressure per pad (0–1) |
| imu | 250 Hz | `(acc[3], gyro[3])` | Per-segment inertial data (raw counts) |

## 3. The data package

`device.stream()` returns a context manager that yields `Frame` objects. Each frame bundles the latest sample from all three streams, timestamped to the host clock at the moment of arrival.

```python
with device.stream() as frames:
    for frame in frames:
        print(frame.t)      # host timestamp, seconds since epoch
        print(frame.q)      # joint angles, shape (N_dofs,)
        print(frame.touch)  # contact pressures, shape (N_pads,)
        print(frame.imu)    # dict: {"acc": array, "gyro": array}
```

!!! note
    The frame bundles all modalities even though they run at different rates. When a faster stream (IMU at 250 Hz) produces data between kinematics frames (100 Hz), the SDK holds the latest IMU sample and attaches it to the next kinematics frame. This means `frame.imu` is always present but may repeat across consecutive kinematics frames.

## 4. Three sync scopes

Chiros supports hardware-assisted synchronization at three levels of scope. Most applications only need intra-device sync, which is on by default.

| Scope | Status | What it covers |
|---|---|---|
| Intra-device | Core | All sensors within a single Chiros unit share one hardware clock. Always active. |
| User | Supported | Two Chiros units (left + right) synchronized via the external SYNC cable. |
| Group | Experimental | Multiple pairs of units plus external trackers. API subject to change. |

## 5. Host clock

All timestamps in the SDK (`frame.t`) are in seconds since the Unix epoch, measured on the host machine using a monotonic clock corrected to wall time at connection open. The device's internal microsecond counter is used only to timestamp samples relative to each other within a packet; the host clock is the authoritative reference for all inter-frame and cross-device comparisons.

If the host clock is synchronized to a network time server (NTP or PTP), `frame.t` values are directly comparable across machines.

## Where to go next

- [API reference](sdk-api-reference.md) — full Python surface with all parameters and return types.
- [Bimanual recording](guide-bimanual.md) — how to use user-scope sync with two devices.
- [ROS2 integration](integrations-ros2.md) — how frames map to ROS2 message types.
