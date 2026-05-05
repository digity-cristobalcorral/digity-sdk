---
eyebrow: Getting Started
lede: "What the host computer needs to run the SDK and capture data without dropping frames, and what the device exposes physically."
---

# System Requirements

## Host operating system

| OS | Status | Notes |
|---|---|---|
| Ubuntu 22.04 / 24.04 | Supported | Recommended for teleoperation and ROS2 work. |
| macOS 14+ | Supported | Tested on Apple Silicon and Intel. |
| Windows 11 WSL2 | Best effort | USB passthrough via usbipd required. |
| Windows 11 native | Not supported | Use WSL2 or a Linux machine. |

## Runtime

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12 |
| USB | 3.0 | 3.2 Gen2 |
| RAM | 4 GB | 8 GB |
| Disk | ~600 MB | ~5 GB |

## Device-side interface

Chiros exposes two physical connectors on the forearm plate. All data travels over the required USB-C connection; the SYNC jack is optional and used only for multi-device or external-tracker workflows.

| Interface | Connector | Purpose |
|---|---|---|
| Host USB-C | USB-C (required) | Power, data, firmware update |
| External SYNC | 3.5 mm stereo jack (optional) | Hardware sync pulse in/out for multi-device or external-tracker workflows |

## Data rates

The firmware streams three data channels continuously at the rates below. These are target rates; the actual rate on the host depends on USB scheduling and host CPU load.

| Modality | Target rate | Notes |
|---|---|---|
| Kinematics | 100 Hz | All DOFs, both hands if bimanual |
| Touch | 30–100 Hz | Rate is configurable; higher rates reduce SNR |
| IMU | 250 Hz | Per-segment; downsampled to 100 Hz in the default SDK config |

## Real-time considerations

For most research use cases the default Python SDK is sufficient. The SDK's background serial thread keeps the read buffer from overflowing; the main thread processes frames at whatever rate the application can sustain.

{% hint style="info" %}
For bimanual teleoperation at 100 Hz, latency becomes important. Pin the streaming thread to an isolated CPU core and set the process to `SCHED_FIFO` priority. On Ubuntu, install `linux-lowlatency` for sub-millisecond scheduling jitter. See [Bimanual recording](guide-bimanual.md) for a worked example.
{% endhint %}
