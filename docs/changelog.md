---
eyebrow: SDK
lede: SDK and dashboard releases. Newest first.
---

<div class="release">
<div class="release__h"><div class="release__v">SDK 0.2.5</div><div class="release__d">2025 · 05 · 04</div></div>
<p class="muted">Multiview dashboard with 4 hands, nav updates, 3D models.</p>

- **New:** Multiview page with up to 200 side-by-side hand instances (`/chiros/multiview`).
- **New:** Ability Hand and Schunk SVH 3D models.
- Navigation and template improvements.
</div>

<div class="release">
<div class="release__h"><div class="release__v">SDK 0.2.3</div><div class="release__d">2025 · 04 · 23</div></div>
<p class="muted">Platform-specific requirements documented.</p>

- README and DOCS updated with Windows and Linux installation instructions.
- GTK system package requirements for `digity[viz]` on Linux.
</div>

<div class="release">
<div class="release__h"><div class="release__v">SDK 0.2.2</div><div class="release__d">2025 · 04 · 23</div></div>
<p class="muted">Agent mode, dashboard recording, recordings folder.</p>

- **New:** Agent relay — `digity-viz --agent --token TOKEN` streams to a remote server.
- **New:** `digity-agent` CLI for standalone relay without the local dashboard.
- **New:** Session recording to `~/digity-recordings/` as JSONL.
- **New:** Setup page for port configuration and agent token management.
</div>

<div class="release">
<div class="release__h"><div class="release__v">SDK 0.2.0</div><div class="release__d">2025 · 04 · 01</div></div>
<p class="muted">digity[viz] web dashboard, GlovePublisher ZMQ broadcasting.</p>

- **New:** `digity[viz]` optional extra — Flask + SocketIO dashboard with 3D hand models.
- **New:** `GlovePublisher` — ZMQ PUB socket broadcaster for fan-out to multiple consumers.
- **New:** `GloveStream(host=...)` remote mode — subscribe to a `GlovePublisher` over ZMQ.
- Dashboard always mounted at `/chiros/` prefix.
</div>

<div class="release">
<div class="release__h"><div class="release__v">SDK 0.1.0</div><div class="release__d">2025 · 03 · 01</div></div>
<p class="muted">First public release.</p>

- HUMI binary protocol parser for ESP32 glove firmware.
- `GloveStream` context manager — auto-detects USB serial port.
- Typed dataclasses: `GloveFrame`, `AnglesSensor`, `ImuSensor`, `TouchSensor`.
- Auto-detection of CH340, CP210x, FTDI, and ESP32 built-in USB-serial chips.
</div>
