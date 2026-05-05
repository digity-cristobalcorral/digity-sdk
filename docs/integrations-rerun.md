---
eyebrow: Integrations
lede: Visualize live glove data in Rerun — an animated 3D Inspire Hand model driven by forward kinematics, plus per-finger angle charts, touch, and IMU.
---

## Requirements

```bash
pip install rerun-sdk numpy digity
```

!!! note
    If you have the `rerun` CLI tool installed (a different PyPI package), import resolution may fail. The viewer script detects this and corrects the path automatically. If you still see an `ImportError`, install `rerun-sdk` explicitly.

## Run the viewer

```bash
python examples/rerun_viewer.py           # auto-detect port
python examples/rerun_viewer.py /dev/ttyUSB0
python examples/rerun_viewer.py COM3
```

Rerun spawns its viewer window automatically. Press Ctrl-C to stop.

## Default layout

| Panel | Content |
|---|---|
| Left (3/5) | 3D Spatial view of the animated Inspire Hand model. |
| Top-right | Tabbed time-series: per-finger angle channels (5 joints × 5 fingers). |
| Bottom-right | Touch channels and IMU (acc + gyro) per finger. |

## How the 3D model works

The Inspire Hand model uses rigid GLB mesh pieces — one per link — positioned via a URDF-derived kinematic chain. For each frame, the viewer computes each link's pose by composing the joint's rest quaternion (from URDF RPY angles) with a rotation about the joint axis by the live glove angle:

```python
for jname, _, child, xyz, _, axis in _JOINT_DEFS:
    angle = joint_angles.get(jname, 0.0)
    q = quat_mul(_REST_QUATS[jname], axis_angle_quat(axis, angle))
    rr.log(
        _LINK_PATHS[child],
        rr.Transform3D(translation=xyz, mat3x3=quat_to_mat3(q).tolist()),
    )
```

Glove angle channels map to Inspire Hand joints:

| Finger | Angle channel | Joint |
|---|---|---|
| Thumb (0) | ch[3] — abduction | thumb_proximal_yaw_joint |
| Thumb (0) | ch[0] — MCP flex | thumb_proximal_pitch_joint |
| Thumb (0) | ch[1] — PIP | thumb_intermediate_joint |
| Thumb (0) | ch[2] — DIP | thumb_distal_joint |
| Index–Pinky (1–4) | ch[0] — proximal flex | `<finger>_proximal_joint` |
| Index–Pinky (1–4) | ch[1] — intermediate flex | `<finger>_intermediate_joint` |

## Important: group filter

The viewer filters `frame.group == "hand"` before routing finger angles. Without this filter, arm-sensor packets (wrist/forearm nodes with `finger=0`) would corrupt the thumb animation:

```python
if isinstance(sensor, AnglesSensor):
    if frame.group == "hand":   # ← required: skip arm nodes
        log_angles(sensor.finger, sensor)
```

## Where to go next

- [Dashboard](integrations-dashboard.md) — built-in web dashboard with recording.
- [ROS2 bridge](integrations-ros2.md) — publish joint states as ROS2 topics.
- [SDK · Sensor types](sdk-core-concepts.md#sensor-types-and-finger-index) — group, finger, and channel reference.
