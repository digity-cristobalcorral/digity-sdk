---
eyebrow: Guides
lede: "Two Chiros, one host, one operator. User-scope sync keeps the two hands aligned in real time — not just in post-processing."
---

# Bimanual Recording

## Why real-time alignment matters

When training an imitation-learning policy on bimanual demonstrations, the timestamps of the left and right hand frames must be synchronized to a common clock. If the two devices run on independent host-clock timestamps, sub-millisecond jitter accumulates over a session and introduces correlated noise that degrades policy quality — especially for tasks where the hands must coordinate precisely (e.g., threading a bolt, folding fabric).

User-scope sync uses a hardware pulse on the external SYNC cable to align the two device clocks to within ~10 µs. This is sufficient for all current SDK use cases.

## Wiring

> *[Diagram placeholder: photo of SYNC cable connecting two forearm plates, 3.5 mm TRS jacks]*

Connect the included SYNC cable between the 3.5 mm SYNC jacks on the two forearm plates. Polarity does not matter — either device can be the leader. The SDK assigns the leader automatically based on the order devices are passed to `SyncGroup`.

## Code

```python
import chiros

left  = chiros.Device.open(side="left")
right = chiros.Device.open(side="right")

with chiros.SyncGroup([left, right]):
    with left.stream() as lframes, right.stream() as rframes:
        for frame_l, frame_r in zip(lframes, rframes):
            # frame_l.t and frame_r.t are hardware-synchronized
            process(frame_l, frame_r)
```

`SyncGroup` arms the sync hardware on both devices when the `with` block is entered and disarms it on exit. If the SYNC cable is not connected when `SyncGroup` is entered, it raises `RuntimeError` immediately.

## Identifying left vs right

Each device reports its side in `device.info.side` and in every frame via `frame.device.side`. You do not need to track which variable is "left" or "right" manually; you can look it up at any point.

```python
for frame_l, frame_r in zip(lframes, rframes):
    # safe to rely on — comes from the firmware, not from your variable names
    assert frame_l.device.side == "left"
    assert frame_r.device.side == "right"
```

## Tuning for teleoperation

- **Reduce latency.** Use `device.stream(imu=False)` if the IMU is not needed; this reduces per-frame processing time.
- **Pin to a CPU core.** On Linux, use `taskset -c 2 python your_script.py` to pin the process to an isolated core and reduce scheduling jitter.
- **Use `SCHED_FIFO`.** For sub-millisecond end-to-end latency, set the streaming thread to real-time priority: `sudo chrt -f 50 python your_script.py`. Requires `CAP_SYS_NICE`.

{% hint style="info" %}
Looking ahead: group-scope sync (more than two devices, or Chiros + external trackers) is experimental in SDK 0.4. The `SyncGroup` API accepts more than two devices, but the hardware arbitration protocol is not yet finalized and may change in SDK 0.5. For production bimanual work, stick to two devices with user-scope sync.
{% endhint %}
