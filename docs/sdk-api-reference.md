---
eyebrow: SDK
lede: "The Python surface, organized by what you typically do: discover devices, open them, read streams, synchronize, record."
---

# SDK API Reference

## Discovery & identity

**`chiros.Device.discover() → list[DeviceInfo]`**

Scans all connected USB devices and returns a list of `DeviceInfo` objects for every recognized Chiros unit. Each `DeviceInfo` has `.serial` (str), `.side` ("left" or "right"), and `.firmware` (str). Returns an empty list if no devices are found.

**`chiros.Device.open(serial: str | None = None, side: str | None = None) → Device`**

Opens a connection to a Chiros device. If exactly one device is connected, all arguments are optional. Raises `DeviceNotFoundError` if no matching device is found and `AmbiguousDeviceError` if more than one device matches the criteria.

**`device.info`**

A `DeviceInfo` object for the open device. Read-only. Contains `.serial`, `.side`, `.firmware`, and `.n_dofs` (total degrees of freedom reported by the firmware).

## Streams

**`device.stream(kinematics=True, touch=True, imu=True) → ContextManager[FrameIterator]`**

Opens the data stream and returns a context manager that yields `Frame` objects. Pass `False` for any modality you do not need; this reduces USB bandwidth slightly.

```python
with device.stream() as frames:
    for frame in frames:
        process(frame)
```

Each `Frame` exposes:

- `frame.t` — host timestamp, seconds since epoch (float)
- `frame.q` — joint angles in radians, shape `(N_dofs,)` (NumPy array)
- `frame.touch` — contact pressures 0–1, shape `(N_pads,)` (NumPy array)
- `frame.imu` — dict with keys `"acc"` and `"gyro"`, each shape `(N_segments, 3)`

**`frame.stale() → bool`**

Returns `True` if this frame contains no new kinematics data since the previous frame (i.e., the kinematics stream underran). Useful for detecting drop events without raising an exception.

## Synchronization

**`chiros.SyncGroup(devices: list[Device]) → ContextManager`**

Arms user-scope hardware sync across a list of devices. Requires a SYNC cable connecting the forearm plates of all devices. The first device in the list becomes the sync leader; all others are followers.

```python
left = chiros.Device.open(side="left")
right = chiros.Device.open(side="right")

with chiros.SyncGroup([left, right]):
    with left.stream() as lf, right.stream() as rf:
        for frame_l, frame_r in zip(lf, rf):
            # frame_l.t and frame_r.t are hardware-synchronized
            process(frame_l, frame_r)
```

**`device.sync_in.arm(polarity="rising") → None`**

Manually arm the sync input on a single device, accepting either `"rising"` or `"falling"` edge. Used when integrating with an external pulse source (e.g., an MRI trigger or a motion-capture system).

## Recording

**`chiros.Recorder(path: str | Path, metadata: dict | None = None) → ContextManager`**

Opens a `.chiros` recording archive for writing. Accepts an optional `metadata` dict (subject ID, task name, etc.) that is stored in the archive header. Flushes and closes the archive on context exit.

```python
with chiros.Recorder("session_01.chiros", metadata={"subject": "P01"}) as rec:
    with device.stream() as frames:
        for frame in frames:
            rec.write(frame)
```

Load a recording back with `chiros.load("session_01.chiros")`, which returns a list of `Frame` objects.

## Errors

| Exception | Raised when |
|---|---|
| `DeviceNotFoundError` | No connected device matches the requested serial or side. |
| `AmbiguousDeviceError` | More than one device matches and no disambiguating argument was given. |
| `StreamUnderrunError` | The host cannot drain the USB buffer fast enough; frames were dropped. |
| `SyncDriftError` | The hardware sync timestamps between two devices have diverged beyond the configured tolerance. |
