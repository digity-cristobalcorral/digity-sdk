---
eyebrow: Getting Started
lede: A sensorized exohand that captures finger angles, touch, and IMU data in real time over USB. Built for robotics, teleoperation, and physical AI research.
---

The Digity glove is a wearable instrument that covers one hand — four fingers and thumb — and streams three types of sensor data to a host computer via USB. The ESP32-based firmware encodes sensor readings in the HUMI binary protocol at up to 50 Hz per finger node; the Python SDK decodes them and yields structured `GloveFrame` objects to your application.

The SDK works the moment the glove is plugged in. No homing, no per-session calibration, no cloud dependency. Everything runs locally.

## Sensor streams

| Stream | Type | Description |
|---|---|---|
| Angles | `AnglesSensor` | Joint angles in degrees for each finger (up to 5 channels per node). Used for forward kinematics, teleoperation, and imitation learning. |
| Touch | `TouchSensor` | 6-channel capacitive touch per finger, normalized 0–1. Detects contact and pressure on the fingertip and phalanges. |
| IMU | `ImuSensor` | 6-axis inertial (accelerometer + gyroscope) raw counts per finger node. Useful for impact detection and orientation estimation. |

## Who it is for

The primary audience is anthropomorphic robotics, physical AI, and simulation — researchers and engineers who need high-fidelity hand motion and contact data as input to teleoperation pipelines, imitation-learning datasets, and embodied-AI training.

- **Robot teleoperation** — stream live finger poses into a ROS2 node driving a robot hand.
- **Dataset collection** — record demonstrations with the built-in dashboard and export for training.
- **Simulation** — feed live angles into Isaac Sim, MuJoCo, or Unity for physics-based control.
- **Research** — access the raw sensor stack directly from Python.

## What it is not

- Not a haptic feedback or force-display device — it only senses, it does not actuate.
- Not a medical or clinical device.
- Not a closed system — the full sensor stack is accessible via the Python SDK.

## Where to go next

- [Quickstart](index.md) — from plugged-in glove to a live data stream in five minutes.
- [System requirements](system-requirements.md) — what your host needs.
- [SDK · Core concepts](sdk-core-concepts.md) — the data model and how frames are structured.
