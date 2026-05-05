---
eyebrow: Integrations
lede: "A reference connector built on the Chiros CDK. Publishes the three streams as ROS2 topics on a configurable QoS profile, with sync flags carried as message-level stamps."
---

# ROS2 Integration

## About the CDK

The Chiros SDK ships a stable core API (`chiros.Device`, `chiros.Recorder`, etc.). On top of that sits the CDK (Connector Development Kit), a lower-level layer that exposes the raw frame bus and sync primitives so community contributors can build integrations for specific robot frameworks, simulators, and data-collection pipelines.

The ROS2 connector is the first reference CDK integration. It is maintained by the Chiros team and tested against ROS2 Humble and Jazzy on Ubuntu 22.04 and 24.04. Community-driven connectors for other frameworks (Isaac Lab, Mujoco Simulate, OpenXR) are welcome; see the CDK documentation for the contributor guide.

## Topics

The connector publishes four topics per connected device. Topic names are prefixed with the device serial number when more than one device is connected (e.g., `/chiros/00042/kinematics`).

| Topic | Type | Rate |
|---|---|---|
| `/chiros/kinematics` | `sensor_msgs/JointState` | 100 Hz |
| `/chiros/touch` | `std_msgs/Float32MultiArray` | 30–100 Hz (device-configured) |
| `/chiros/imu` | `sensor_msgs/Imu` | 250 Hz |
| `/chiros/sync` | `std_msgs/Header` | On sync event |

## Launch

```bash
# Single device, auto-detect
ros2 launch chiros_ros2 chiros.launch.py

# Bimanual — two devices, one host
ros2 launch chiros_ros2 chiros.launch.py bimanual:=true

# Explicit serial numbers
ros2 launch chiros_ros2 chiros.launch.py left_serial:=00041 right_serial:=00042
```

For bimanual use, connect the SYNC cable between the two forearm plates before launching. The connector will automatically arm user-scope sync and carry the sync flag in the `header.stamp` of every message.

## Where to go next

- [Bimanual recording](guide-bimanual.md) — user-scope sync and how to wire two devices.
- [SDK core concepts](sdk-core-concepts.md) — how the three streams map to the ROS2 topic types.
- [Troubleshooting](troubleshooting.md) — USB passthrough for WSL2, permission issues on Linux.
