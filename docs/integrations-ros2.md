---
eyebrow: Integrations
lede: A ready-to-use ROS2 package that reads from GloveStream and publishes joint states, IMU, and touch data as standard ROS2 topics.
---

## Overview

The `digity_ros2` package wraps `GloveStream` in a ROS2 node. It runs the serial read loop in a background thread and publishes data at a configurable rate via a timer — decoupling the glove packet rate from the ROS2 publish rate.

The package lives in your ROS2 workspace at `~/ros2_ws/src/digity_ros2/` and requires the Digity SDK (`pip install digity`) in the Python environment sourced by ROS2.

## Topics published

| Topic | Type | Description |
|---|---|---|
| `/joint_states` | `sensor_msgs/JointState` | All 20 finger joint positions in radians, mapped to P50 URDF joint names. Published at `publish_hz` (default 50 Hz). |
| `/digity/imu` | `sensor_msgs/Imu` | Raw IMU (accelerometer + gyroscope i16 counts) per finger. One message per packet. |
| `/digity/touch` | `std_msgs/Float32MultiArray` | Touch channels 0–1, 6 per finger. One message per packet. |

## Build and install

```bash
# Install the SDK into the ROS2 Python environment
pip install digity

# Build the ROS2 package
cd ~/ros2_ws
colcon build --packages-select digity_ros2
source install/setup.bash
```

## Launch

```bash
# Auto-detect glove port
ros2 launch digity_ros2 digity.launch.py

# Explicit serial port
ros2 launch digity_ros2 digity.launch.py port:=/dev/ttyUSB0

# Glove on remote machine
ros2 launch digity_ros2 digity.launch.py host:=192.168.1.10

# Right hand only, 100 Hz
ros2 launch digity_ros2 digity.launch.py side:=right publish_hz:=100.0
```

All parameters:

| Parameter | Default | Description |
|---|---|---|
| `port` | `""` | Serial port (empty = auto-detect). |
| `host` | `""` | ZMQ host IP for remote mode. Overrides `port`. |
| `publish_hz` | `50.0` | `/joint_states` publish rate in Hz. |
| `side` | `""` | Filter by glove side: `"right"` or `"left"`. Empty = accept both. |

## Joint mapping (P50 URDF)

The node maps `AnglesSensor.samples[-1].angles_deg[i]` to P50 URDF joints, converting degrees to radians and clamping to joint limits.

| Finger | Channel 0 | Channel 1 | Channel 2 | Channel 3 |
|---|---|---|---|---|
| Thumb (0) | thumb_base2cmc | thumb_cmc2mcp | thumb_mcp2pp | thumb_pp2dp_actuated |
| Index (1) | index_base2mcp | index_mcp2pp | index_pp2mp | index_mp2dp |
| Middle (2) | middle_base2mcp | middle_mcp2pp | middle_pp2mp | middle_mp2dp |
| Ring (3) | ring_base2mcp | ring_mcp2pp | ring_pp2mp | ring_mp2dp |
| Pinky (4) | pinky_base2mcp | pinky_mcp2pp | pinky_pp2mp | pinky_mp2dp |

!!! note
    Only `frame.group == "hand"` packets are routed to joint angles. Arm-group packets (wrist/forearm) are ignored in joint state publishing.

## Architecture

The serial read loop runs in a daemon thread that writes to a shared `dict` protected by a `threading.Lock`. The ROS2 publish timer reads from the same dict at a fixed rate. This decouples the packet arrival rate (~50 Hz) from the publish rate, preventing the ROS2 spin loop from blocking on serial I/O.

## Where to go next

- [Rerun viewer](integrations-rerun.md) — visualize glove data in 3D with the Inspire Hand model.
- [SDK · Core concepts](sdk-core-concepts.md) — the data model the node translates from.
