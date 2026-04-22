"""
GlovePublisher — broadcasts GloveFrame objects over a ZMQ PUB socket.

Subscribers connect with GloveStream(host="<ip>").

Standalone use (just publish, no web UI):
    from digity import GlovePublisher

    with GlovePublisher() as pub:
        pub.run()   # blocks; Ctrl+C to stop

Embedded use (publish alongside other processing):
    with GlovePublisher() as pub:
        with GloveStream() as stream:
            for frame in stream:
                pub.publish(frame)
                # ... your processing here
"""

from __future__ import annotations

import json
import threading
from typing import Optional

from ._types import AnglesSensor, GloveFrame, ImuSensor, TouchSensor

DEFAULT_ZMQ_PORT = 5555


def _frame_to_payload(frame: GloveFrame) -> bytes:
    sensors = []
    for s in frame.sensors:
        if isinstance(s, AnglesSensor):
            sensors.append({
                "type":    "angles",
                "finger":  s.finger,
                "com":     s.com,
                "samples": [{"ts_us": sa.ts_us, "angles_deg": sa.angles_deg}
                            for sa in s.samples],
            })
        elif isinstance(s, ImuSensor):
            sensors.append({
                "type":    "imu6",
                "finger":  s.finger,
                "com":     s.com,
                "samples": [{"ts_us": sa.ts_us, "acc": list(sa.acc), "gyro": list(sa.gyro)}
                            for sa in s.samples],
            })
        elif isinstance(s, TouchSensor):
            sensors.append({
                "type":         "touch6",
                "finger":       s.finger,
                "com":          s.com,
                "ts_us":        s.ts_us,
                "channels":     s.channels,
                "channels_raw": s.channels_raw,
            })
    msg = {
        "type": "sensor_frame",
        "ts": frame.ts,
        "frame": {
            "side":    frame.side,
            "group":   frame.group,
            "node_id": frame.node_id,
            "seq":     frame.seq,
            "sensors": sensors,
        },
    }
    return json.dumps(msg, separators=(",", ":")).encode()


class GlovePublisher:
    """
    Publishes GloveFrame data over a ZMQ PUB socket.

    Topic  : b"sensor"
    Payload: JSON {"ts": float, "frame": {side, group, node_id, seq, sensors}}

    Subscribers connect with GloveStream(host="<ip>", zmq_port=5555).
    """

    def __init__(
        self,
        zmq_port: int = DEFAULT_ZMQ_PORT,
        bind: str = "tcp://*",
    ) -> None:
        self._zmq_port = zmq_port
        self._bind     = bind
        self._ctx      = None
        self._sock     = None
        self._lock     = threading.Lock()

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> "GlovePublisher":
        """Open the ZMQ PUB socket and start listening for subscribers."""
        try:
            import zmq
        except ImportError:
            raise ImportError("pyzmq is required. Run:  pip install pyzmq")
        self._ctx  = zmq.Context()
        self._sock = self._ctx.socket(zmq.PUB)
        self._sock.bind(f"{self._bind}:{self._zmq_port}")
        return self

    def stop(self) -> None:
        """Close the ZMQ socket."""
        with self._lock:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
            if self._ctx:
                try:
                    self._ctx.term()
                except Exception:
                    pass
                self._ctx = None

    def __enter__(self) -> "GlovePublisher":
        return self.start()

    def __exit__(self, *_) -> None:
        self.stop()

    # ── Publishing ─────────────────────────────────────────────────────────────

    def publish(self, frame: GloveFrame) -> None:
        """Publish one frame. Non-blocking; dropped silently if socket is closed."""
        import zmq
        with self._lock:
            if self._sock is None:
                return
            try:
                self._sock.send_multipart(
                    [b"sensor", _frame_to_payload(frame)],
                    flags=zmq.NOBLOCK,
                )
            except Exception:
                pass

    # ── Standalone blocking runner ─────────────────────────────────────────────

    def run(self, port: Optional[str] = None, baud: int = 921600) -> None:
        """
        Read from serial and publish until interrupted.
        Blocks the calling thread; stop with Ctrl+C or by calling stop() from
        another thread.
        """
        import time
        from ._serial import SerialReader
        from ._stream import _parse_frame

        reader = SerialReader(port=port, baud=baud)
        reader.start()
        print(f"[GlovePublisher] ZMQ PUB bound on {self._bind}:{self._zmq_port}")
        try:
            while reader._running:
                if reader._error:
                    raise reader._error
                try:
                    raw = reader.queue.get(timeout=1.0)
                except Exception:
                    continue
                frame = _parse_frame(raw, ts=time.time())
                if frame is not None:
                    self.publish(frame)
        except KeyboardInterrupt:
            pass
        finally:
            reader.stop()
