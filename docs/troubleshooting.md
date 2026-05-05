---
eyebrow: Support
lede: "The most common things that go wrong, what they mean, and how to fix them. Roughly ordered by frequency."
---

# Troubleshooting

## Device not detected

`chiros.Device.discover()` returns an empty list, or `chiros.Device.open()` raises `DeviceNotFoundError`.

- **Cable.** Try a different USB-C cable. Some USB-C cables are power-only and carry no data. Use the cable included with the device or one rated for USB 3.0 data.
- **Port.** Connect directly to a USB port on the host machine. USB hubs — especially unpowered ones — can prevent the device from enumerating correctly.
- **Permissions (Linux).** The device appears as a USB-serial interface. Your user must have read/write access: copy the udev rules file from the package and reload (`sudo udevadm control --reload-rules && sudo udevadm trigger`), then unplug and replug the device.
- **WSL2.** USB devices are not automatically passed through to WSL2. Install `usbipd-win` on Windows and attach the device: `usbipd attach --wsl --busid <id>`.

## StreamUnderrunError

The host cannot drain the USB buffer fast enough and frames were dropped.

- Move any heavy computation out of the main frame loop and into a worker thread or process.
- If you only need kinematics, open the stream with `device.stream(touch=False, imu=False)` to reduce per-frame work.
- On a heavily loaded machine, set the streaming thread to a higher OS priority or pin it to an isolated CPU core.

## SyncDriftError on bimanual

Two synchronized devices have drifted beyond the configured tolerance.

- Check that the SYNC cable is fully seated in both 3.5 mm jacks. A loose connection causes intermittent sync loss.
- The default drift tolerance is 500 µs. If your use case tolerates more, pass `tolerance_us=2000` to `SyncGroup`.
- Do not run both devices through the same USB hub. Each device should connect directly to the host or to separate powered hubs.

## NaN in q[mcp_abd]

The MCP abduction/adduction channel reads `NaN` for fingers II–V.

This is a known firmware limitation in v0.4. The 6-bar linkage at the MCP joint mechanically couples abduction to flexion; the firmware does not yet separate the two. The channel is reserved and will return valid data in a future firmware release. For now, ignore `q[mcp_abd]` for fingers II–V and use only the flexion channels.

## Touch column sparsely populated

`frame.touch` contains many zeros even when the finger is clearly in contact.

The touch sensor rate is configurable and defaults to 50 Hz. At high contact forces the ADC can saturate and clip to zero; reduce the excitation voltage in the firmware settings page of the Chiros Viewer. Also check that the digit module is seated flush against the finger — a gap of more than ~2 mm reduces coupling significantly.

## External SYNC pulse not landing

`device.sync_in.arm()` is called but frames do not show a sync event.

- Verify the pulse polarity. The default is `"rising"`. If your source generates a falling-edge pulse, pass `polarity="falling"`.
- The SYNC input expects a 3.3 V logic signal on the tip of the 3.5 mm jack (TRS: tip = signal, ring = ground, sleeve = ground). Check your cable wiring.
- The minimum pulse width is 10 µs. Pulses shorter than this may not be detected.

## Still stuck?

Open an issue on [github.com/digity-de/chiros-sdk](https://github.com/digity-de/chiros-sdk) with the output of `chiros doctor` and a description of what you tried.
