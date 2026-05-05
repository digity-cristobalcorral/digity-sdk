---
eyebrow: Getting Started
lede: From plugged-in glove to a live Python data stream in under five minutes.
---

## What you'll need

- Your Digity glove and the included USB cable.
- A workstation running Ubuntu 22.04+, Debian 11+, or Windows 10/11.
- Python 3.9 or higher.

## Install the SDK

```bash
# Core SDK — serial reading only (pyserial + pyzmq)
pip install digity

# Linux: install system packages first (for the web dashboard)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
pip install "digity[viz]"
```

!!! note
    The GTK system packages must be installed **before** creating your virtual environment, or use `python3 -m venv .venv --system-site-packages` so the venv can find them. See [System requirements](system-requirements.md) for details.

## Connect the glove

Plug the glove into a USB port. On Linux, make sure your user is in the `dialout` group:

```bash
# Add your user to the dialout group (log out and back in after)
sudo usermod -aG dialout $USER

# Verify the glove is detected
python -c "from digity._serial import find_glove_port; print(find_glove_port())"
```

On Windows the port is detected automatically — no extra setup needed.

## Open your first stream

```python
from digity import GloveStream, AnglesSensor

# auto-detects the USB port
with GloveStream() as stream:
    for frame in stream:
        for sensor in frame.sensors:
            if isinstance(sensor, AnglesSensor):
                print(f"finger {sensor.finger}: {sensor.samples[-1].angles_deg}")
```

You should see lines like `finger 1: [12.4, 34.1, 28.0, 5.3, 0.0]` that change when you move your fingers.

## Launch the dashboard

The optional `digity[viz]` extra includes a real-time 3D web dashboard:

```bash
# opens desktop window (or browser if no display)
digity-viz

# open in system browser instead
digity-viz --browser

# fallback on Windows if CLI is not on PATH
python -m digity.viz
```

The dashboard is always served at `http://127.0.0.1:5001/chiros/`.

## Where to go next

- [Core concepts](sdk-core-concepts.md) — understand frames, sensors, and data types.
- [API reference](sdk-api-reference.md) — the full Python surface.
- [ROS2 integration](integrations-ros2.md) — publish glove data as ROS2 topics.
- [Dashboard guide](integrations-dashboard.md) — recording, remote streaming, and agent mode.
