---
eyebrow: "Hardware Reference · Digits II–V"
lede: "Each finger (index, middle, ring, pinky) is a three-segment chain worn on the ulnar side of the digit. A 6-bar linkage at the MCP creates a virtual center of rotation, so the device fits different hands without physical alignment."
---

# Finger Architecture

> *[Diagram placeholder: GIF · single index finger, side view]*

## Segments

Each finger module consists of three rigid PCB segments connected by flex-PCB bridges. The segments sit on the dorsal side of the finger and are held in place by a silicone retention sleeve that slips over each phalanx.

| Segment | Phalanx | Distal joint | Sensorized |
|---|---|---|---|
| Distal | Distal phalanx | DIP (distal interphalangeal) | Touch (fingertip pad) |
| Medial | Middle phalanx | PIP (proximal interphalangeal) | Angle |
| Proximal | Proximal phalanx | MCP (metacarpophalangeal) | Angle, IMU |

## The 6-bar linkage at the MCP

The metacarpophalangeal joint of a finger moves in two axes: flexion/extension and abduction/adduction. The center of rotation shifts as the joint angle changes, which means a simple pivot attached to the dorsal surface would bind against the finger during flexion.

Chiros solves this with a 6-bar linkage. The proximal segment is not attached directly to the hand plate; instead, it is connected through a four-bar sub-linkage that tracks the MCP's changing center of rotation. This allows the device to move with the finger without applying a resistive moment that would alter the natural kinematics.

> *[Diagram placeholder: schematic of the 6-bar linkage, side view]*

The linkage is calibrated at the factory for the median hand size. No user adjustment is required. The flex-PCB that spans the linkage carries the angle sensor that reads the MCP flexion angle. A second sensor on the transverse bar reads abduction.

{% hint style="info" %}
Design note: the 6-bar approach adds two passive links compared to a direct-attach design. This increases part count but eliminates the need for per-user alignment and makes the device size-agnostic within the supported hand range. The tradeoff was validated against direct kinematics in the original research paper (see the Resources page).
{% endhint %}

## Specifications

| Property | Value |
|---|---|
| Covered digits | II, III, IV, V (index through pinky) |
| Segments per finger | 3 (distal, medial, proximal) |
| Angle sensors per finger | 3 (MCP flex, PIP, DIP) |
| Touch pads per finger | 1 (distal segment, fingertip) |
| IMU per finger | 1 (proximal segment) |
| Total DOFs per finger | 3 flexion + 1 abduction (reserved in v0.4) |

{% hint style="warning" %}
In SDK v0.4 and firmware v0.4.x, the MCP abduction/adduction channel (`q[mcp_abd]`) returns `NaN` for all fingers II–V. The channel is reserved and will be populated in a future firmware release. Do not use it for analysis or control.
{% endhint %}

## Where to go next

- [Hardware overview](hardware-overview.md) — how the finger modules connect to the hand and forearm plates.
- [SDK core concepts](sdk-core-concepts.md) — how the angle channels map to the `frame.q` array.
- [Troubleshooting](troubleshooting.md) — what to do if a segment is missing from the firmware enumeration.
