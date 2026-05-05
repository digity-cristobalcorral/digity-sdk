---
eyebrow: Getting Started
lede: "A hand and forearm exoskeleton that captures high-fidelity hand motion and contact data, time-synchronized, over USB-C. Built for the people training tomorrow's robots."
---

# What is Chiros

Chiros is a wearable scientific instrument. It captures the angles of every finger joint, the contact forces distributed across the fingertips and palm, and the inertial state of the wrist — all synchronized to a single host clock — and streams that data to a host computer over a single USB-C cable.

It is designed to be worn by a human operator during dexterous manipulation tasks. The resulting dataset encodes not just what the hand did, but how it felt: which surfaces were contacted, how hard, and in what sequence.

## Who it is for

Chiros is built around three priorities:

- **Robotics researchers** who need high-quality human demonstration data for imitation learning and teleoperation pipelines.
- **Neuroscience and rehabilitation labs** who need calibrated kinematic and somatosensory data without the marker-placement burden of optical motion capture.
- **Hardware teams** building dexterous robot hands who need a ground-truth reference for benchmarking joint-level controllers.

## Research Edition

The current product is the Research Edition. It ships as a single-hand unit (left or right, specified at order time) with all five digit modules, the wrist bracket, the forearm plate, a USB-C cable, and a quick-start card. A bimanual kit — two units plus a sync cable — is available separately.

Firmware and SDK are under active development. The changelog tracks every breaking change.

## What it is not

- A consumer fitness tracker or gesture remote.
- A device that works wirelessly out of the box (USB-C only in the Research Edition).
- A full-arm exoskeleton — Chiros covers the hand and wrist only.
- A haptic feedback device — it captures data; it does not actuate.

## Where to go next

- [Hardware overview](hardware-overview.md) — what each physical part does.
- [Quickstart](index.md) — install the SDK and open a live data stream.
- [SDK core concepts](sdk-core-concepts.md) — the five ideas that explain the API.
