---
eyebrow: SDK
lede: "SDK and firmware releases for the Chiros Research Edition. Newest first."
---

# Changelog

### SDK 0.4.2 · fw 0.4.2 — 2026 · 04 · 28

Maintenance release.

- Fixed a rare `SyncDriftError` false positive when the host clock stepped backward (NTP correction during a long session).
- `chiros doctor` now reports the USB bus speed and warns if the device is on a USB 2.0 hub.
- Wheels now ship for Python 3.13.

### SDK 0.4.0 · fw 0.4.0 — 2026 · 03 · 11

User-scope sync, public CDK preview.

- **New:** User-scope hardware sync via the external SYNC cable (`chiros.SyncGroup`). Two devices can now share a hardware clock over the 3.5 mm jack.
- **New:** `SyncDriftError` raised when synchronized devices drift beyond the configured tolerance.
- **New:** CDK (Connector Development Kit) preview — `chiros.cdk` module for building custom integrations. API is unstable and subject to change.
- **Breaking:** `Device.stream()` now raises `StreamUnderrunError` instead of silently dropping frames when the USB buffer overflows. Wrap in a try/except or use `frame.stale()` to handle gracefully.
- `Recorder` archive format updated to v2; v1 archives can be read but not written.

### SDK 0.3.0 · fw 0.3.1 — 2025 · 12 · 02

First public SDK.

- Initial release of the `chiros` Python package on PyPI.
- `Device.discover()`, `Device.open()`, `device.stream()`, and `chiros.Recorder` APIs established.
- `chiros doctor` CLI command for device health checks.
