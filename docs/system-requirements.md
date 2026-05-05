---
eyebrow: Getting Started
lede: What your host computer needs to run the SDK and the optional web dashboard without dropping sensor frames.
---

## Host operating system

| OS | Core SDK | digity[viz] | Notes |
|---|---|---|---|
| Ubuntu 22.04 / 24.04 | ✓ Supported | ✓ Supported | Recommended for teleoperation and ROS2 work. Requires system GTK packages for viz. |
| Debian 11 / 12 | ✓ Supported | ✓ Supported | Same GTK requirements as Ubuntu. |
| Windows 10 / 11 | ✓ Supported | ✓ Supported | No extra system packages. If CLI missing from PATH, use `python -m digity.viz`. |
| macOS 13+ | ✓ Supported | Best effort | Core SDK tested. pywebview may require Rosetta on Apple Silicon. |

## Runtime

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.9 | 3.11 or 3.12 |
| USB port | USB 2.0 | USB 3.0+ |
| RAM | 2 GB free | 4 GB free |

## Linux: system packages for digity[viz]

The web dashboard uses **pywebview** (GTK backend) to open a desktop window. The GTK Python bindings are not on PyPI and must come from the system package manager.

```bash
# Run BEFORE creating a virtual environment
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Then either install normally:

```bash
pip install "digity[viz]"
```

Or, if using a venv that needs access to the system packages:

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install "digity[viz]"
```

!!! note
    On a server without a display, the dashboard starts and prints its URL but skips the window. Access via SSH tunnel: `ssh -L 5001:127.0.0.1:5001 user@server`, then open `http://localhost:5001/chiros/` locally.

## Serial port permissions (Linux)

The glove appears as a USB-serial device (`/dev/ttyUSB0` or `/dev/ttyACM0`). Your user must be in the `dialout` group:

```bash
sudo usermod -aG dialout $USER
# log out and log back in for the change to take effect
```

The SDK auto-detects the port by scanning for known USB-serial chip vendor IDs (CH340, CP210x, FTDI, ESP32 built-in).

## Data rates

| Stream | Typical rate | Notes |
|---|---|---|
| Angles (per finger) | ~50 Hz | Up to 5 joint channels per finger node. |
| Touch (per finger) | ~50 Hz | 6 capacitive channels per finger, normalized 0–1. |
| IMU (per finger) | ~50 Hz | Accelerometer + gyroscope, raw i16 counts. |

All sensor packets are time-stamped by the host on receive. Frame queue size is 2000 entries; old frames are dropped when the consumer falls behind.
