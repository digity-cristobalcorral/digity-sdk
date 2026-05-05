---
eyebrow: Getting Started
lede: "Chiros covers one hand. Five digit modules attach to a hand plate; the hand plate articulates with the wrist via a C-shaped bracket; the bracket connects to a forearm plate that houses the electronics and the host port."
---

# Hardware Overview

> *[Diagram placeholder: GIF · full device, dorsal view]*

## Anatomy

Chiros is made up of five digit modules, a hand plate, a C-shaped wrist bracket, and a forearm plate. The digit modules clip onto the dorsal side of each finger. The hand plate ties the digit modules together and acts as the rigid reference frame for the whole hand. The C-bracket allows the hand plate to flex relative to the forearm during wrist extension and flexion. The forearm plate houses the main PCB, the USB-C host port, and the SYNC jack.

| Module | Side | What it provides |
|---|---|---|
| Digits II–V | Dorsal, ulnar | Finger flexion/extension angles, fingertip touch, per-phalanx IMU |
| Digit I | Dorsal, radial | Thumb CMC and MCP angles, fingertip touch |
| Hand plate | Dorsal | Rigid chassis; connects digit modules; palm touch array |
| Wrist bracket | Dorsal | Wrist flexion/extension and radial/ulnar deviation angles |
| Forearm plate | Dorsal forearm | Electronics housing; USB-C host port; external SYNC jack |

## The endoskeleton

Each digit module contains two or three PCB segments that act as rigid phalanges. Flex-PCB bridges span each joint and carry both the signal bus and the mechanical flex load. This means the device has no separate hinge hardware — the PCB itself is the structure.

The PCB segments are sized to fit the 5th–95th percentile adult hand without adjustment. For hands outside that range, replacement segments in two additional sizes are available as accessories.

{% hint style="info" %}
All segments communicate over a proprietary high-speed bus that runs on the same flex-PCB conductors that carry power. You do not need to configure the bus; the firmware auto-enumerates all segments at boot and reports a fault if any are missing.
{% endhint %}

## Tracker mount

The forearm plate has a standardized 1/4-20 mount on the ulnar edge for attaching an external 6-DOF tracker (e.g., an OptiTrack or Vicon rigid body, or a Polhemus sensor). Chiros does not include a tracker; it provides the mount and a hardware SYNC input so the tracker's timestamps can be referenced to the Chiros host clock.

## Where to go next

- [Finger architecture](finger-architecture.md) — how each digit module works mechanically.
- [Troubleshooting](troubleshooting.md) — if the device is not recognized or streams are missing.
