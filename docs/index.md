---
eyebrow: Getting Started
lede: "From sealed box to a live data stream in under fifteen minutes."
---

# Quickstart

## What you'll need

- Chiros unit and USB-C cable (included in the box).
- Ubuntu 22.04+ or macOS 14+.
- Python 3.10+.

## Install the SDK

```bash
pip install chiros

# Linux: configure udev so your user can access the device without sudo
sudo cp /path/to/chiros/udev/99-chiros.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Connect & verify

Plug the Chiros unit into a USB-C port, then run the built-in doctor:

```bash
chiros doctor
```

Expected output:

```
✓ Device found: Chiros-R  fw 0.4.2  sn 00042
✓ Kinematics stream OK  (100 Hz, 0 drops)
✓ Touch stream OK  (50 Hz, 0 drops)
✓ IMU stream OK  (250 Hz, 0 drops)
```

## Open your first stream

Open a Python file and paste the following. `KinematicStream` yields one frame per device cycle at roughly 100 Hz.

```python
import chiros

device = chiros.Device.open()

with device.stream() as frames:
    for frame in frames:
        print(frame.t, frame.q)
```

`frame.q` is a NumPy array of joint angles in radians. Press Ctrl+C to stop.

## Record a session

`Recorder` writes a self-describing archive that bundles kinematics, touch, and IMU into a single file.

```python
import chiros

device = chiros.Device.open()

with chiros.Recorder("my_session.chiros") as rec:
    with device.stream() as frames:
        for frame in frames:
            rec.write(frame)
```

Open the resulting `.chiros` file with the Chiros Viewer or load it back with `chiros.load("my_session.chiros")`.

## Where to go next

- [Bimanual recording](guide-bimanual.md) — two hands, one host, real-time sync.
- [ROS2 integration](integrations-ros2.md) — publish streams as ROS2 topics.
