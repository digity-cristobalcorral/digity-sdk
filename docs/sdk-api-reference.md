---
eyebrow: SDK
lede: The complete Python surface — open a stream, read sensor data, broadcast over ZMQ, handle errors.
---

## GloveStream

<div class="apisig"><div class="apisig__name"><code>GloveStream(port: str | None = None, host: str | None = None)</code></div></div>

Context manager that yields `GloveFrame` objects on every iteration.

| Parameter | Description |
|---|---|
| `port` | Serial port path (`"/dev/ttyUSB0"`, `"COM3"`). Pass `None` to auto-detect. |
| `host` | ZMQ host IP for remote mode. Connects to `tcp://<host>:5555`. Overrides `port`. |

```python
from digity import GloveStream, GloveNotFoundError

try:
    with GloveStream() as s:
        for frame in s:
            ...
except GloveNotFoundError as e:
    print(f"no glove found: {e}")
```

## GloveFrame

<div class="apisig"><div class="apisig__name"><code>frame.ts → float</code></div></div>

Host timestamp in seconds since epoch, set when the packet is received from the serial buffer.

<div class="apisig"><div class="apisig__name"><code>frame.side → str</code></div></div>

`"right"` or `"left"` — which hand this packet came from.

<div class="apisig"><div class="apisig__name"><code>frame.group → str</code></div></div>

`"hand"` or `"arm"`. Always filter `frame.group == "hand"` before routing finger angle data.

<div class="apisig"><div class="apisig__name"><code>frame.seq → int</code></div></div>

Packet counter 0–65535, wraps around. Use to detect drops.

<div class="apisig"><div class="apisig__name"><code>frame.sensors → list[Sensor]</code></div></div>

Sensor objects in this packet. Dispatch with `isinstance`.

## AnglesSensor

<div class="apisig"><div class="apisig__name"><code>sensor.finger → int</code></div></div>

Finger index 0–4 (thumb–pinky).

<div class="apisig"><div class="apisig__name"><code>sensor.samples → list[AnglesSample]</code></div></div>

One or more batched samples. Use `samples[-1]` for the latest.

<div class="apisig"><div class="apisig__name"><code>sample.angles_deg → list[float]</code></div></div>

Joint angles in degrees. For `group="hand"`, always 5 values (MCP-flex, PIP, DIP, abduction, aux).

<div class="apisig"><div class="apisig__name"><code>sample.ts_us → int</code></div></div>

Sample timestamp in microseconds (device clock).

## ImuSensor

<div class="apisig"><div class="apisig__name"><code>sensor.samples → list[ImuSample]</code></div></div>

<div class="apisig"><div class="apisig__name"><code>sample.acc → tuple[int, int, int]</code></div></div>

Raw accelerometer counts (i16), axes X/Y/Z.

<div class="apisig"><div class="apisig__name"><code>sample.gyro → tuple[int, int, int]</code></div></div>

Raw gyroscope counts (i16), axes X/Y/Z.

## TouchSensor

<div class="apisig"><div class="apisig__name"><code>sensor.channels → list[float]</code></div></div>

6 capacitive values normalized 0–1.

<div class="apisig"><div class="apisig__name"><code>sensor.channels_raw → list[int]</code></div></div>

Raw 12-bit ADC counts (0–4095).

<div class="apisig"><div class="apisig__name"><code>sensor.ts_us → int</code></div></div>

## GlovePublisher

<div class="apisig"><div class="apisig__name"><code>GlovePublisher(port: int = 5555, host: str = "127.0.0.1")</code></div></div>

Context manager that opens a ZMQ PUB socket.

<div class="apisig"><div class="apisig__name"><code>pub.publish(frame: GloveFrame) → None</code></div></div>

Serialize and broadcast one frame to all ZMQ subscribers.

<div class="apisig"><div class="apisig__name"><code>pub.run() → None</code></div></div>

Open a `GloveStream` internally and publish every frame. Blocks until Ctrl-C.

## Errors

| Exception | Raised when |
|---|---|
| `GloveNotFoundError` | No USB-serial glove device was found on the host. Check cable and `dialout` group membership. |

## Type alias

<div class="apisig"><div class="apisig__name"><code>Sensor = Union[AnglesSensor, ImuSensor, TouchSensor]</code></div></div>

Exported for type annotations.
