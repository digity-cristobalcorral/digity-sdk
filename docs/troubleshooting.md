---
eyebrow: Support
lede: The most common things that go wrong, what they mean, and how to fix them.
---

## Glove not detected (GloveNotFoundError)

`GloveStream()` raises `GloveNotFoundError`, or `find_glove_port()` returns `None`.

- **Cable.** Try a different USB cable. Data-capable cables only — some USB-C cables are power-only.
- **Port.** Plug directly into the host USB port, not through a hub.
- **Permissions (Linux).** Your user must be in the `dialout` group: `sudo usermod -aG dialout $USER`, then log out and back in.
- **Verify detection.** Run `python -c "from digity._serial import find_glove_port; print(find_glove_port())"`.
- **List all ports.** Run `python -m serial.tools.list_ports -v` to inspect all USB-serial devices.

## Stream opens but no frames arrive

The `for frame in stream:` loop blocks indefinitely without yielding.

- The glove firmware may not be running. Check that the status LED is active.
- Baud rate mismatch — the SDK opens at 921600 baud. If the firmware was flashed with a different rate, communication is silent.

## Thumb angles move unexpectedly

The thumb animation jumps around when you move other fingers or the wrist.

**Cause:** arm-group packets (wrist/forearm sensors) have `finger=0` in their `sens_id`, which looks like thumb data. Fix: always filter by `frame.group == "hand"`.

```python
for sensor in frame.sensors:
    if isinstance(sensor, AnglesSensor):
        if frame.group == "hand":   # ← always check this
            handle_angles(sensor)
```

## Dashboard fails to open on Linux

`digity-viz` crashes with `ModuleNotFoundError: No module named 'gi'`.

- Install system GTK packages: `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1`
- If using a venv, recreate it with `python3 -m venv .venv --system-site-packages`.
- On headless servers, the window is skipped automatically — the server still starts and prints the URL.

## digity-viz command not found (Windows)

- Use the Python module fallback: `python -m digity.viz`
- Or add the Python Scripts folder to PATH: typically `%AppData%\Python\Python3xx\Scripts`.

## ZMQ remote mode — no frames received

`GloveStream(host="192.168.1.10")` blocks without data.

- Ensure the remote machine is running `GlovePublisher` or `digity-viz`.
- The ZMQ PUB socket listens on port 5555. Check firewall rules on both machines.
- ZMQ PUB/SUB is fire-and-forget — if the publisher started before the subscriber, the first few frames may be missed.

## Frames being dropped

The internal queue holds 2000 entries. If your consumer is slower than the glove packet rate, old frames are dropped silently.

- Move heavy processing out of the `for frame in stream:` loop into a worker thread.
- If you only need angles, skip `ImuSensor` and `TouchSensor` to reduce per-frame work.

## Still stuck?

Open an issue on [github.com/digity-cristobalcorral/digity-sdk](https://github.com/digity-cristobalcorral/digity-sdk) or email [cristobal.corral@digity.de](mailto:cristobal.corral@digity.de).
