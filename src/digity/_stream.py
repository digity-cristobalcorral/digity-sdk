"""
GloveStream — main entry point for the digity SDK.

Two modes:
  Serial mode (default):  reads directly from the ESP32 USB port.
                          No other software needed — just plug in the glove.
  ZMQ mode   (advanced):  connects to a running glove-core instance over the network.
                          Useful if the glove is on a remote machine.
"""

from __future__ import annotations

import json
import time
from typing import Iterator, Optional

from ._serial import SerialReader
from ._types import (
    AnglesSample,
    AnglesSensor,
    GloveFrame,
    ImuSample,
    ImuSensor,
    Sensor,
    TouchSensor,
)

DEFAULT_ZMQ_PORT = 5555


class GloveStream:
    """
    Receive live sensor data from the Digity exohand.

    Serial mode — glove plugged directly into this machine (default):
        with GloveStream() as stream:              # auto-detect USB port
            for frame in stream: ...

        with GloveStream(port="/dev/ttyUSB0") as stream:   # explicit port (Linux)
            for frame in stream: ...

        with GloveStream(port="COM3") as stream:           # explicit port (Windows)
            for frame in stream: ...

    ZMQ mode — glove is on a remote machine running glove-core:
        with GloveStream(host="192.168.1.10") as stream:
            for frame in stream: ...

    Each iteration yields one GloveFrame and blocks until the next frame arrives.
    Stop cleanly with Ctrl+C or by calling disconnect() from another thread.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baud: int = 921600,
        *,
        host: Optional[str] = None,
        zmq_port: int = DEFAULT_ZMQ_PORT,
    ) -> None:
        self._use_zmq = host is not None
        self._host    = host
        self._zmq_port = zmq_port

        self._reader: Optional[SerialReader] = None
        self._zmq_sock = None
        self._zmq_ctx  = None

        if not self._use_zmq:
            self._reader = SerialReader(port=port, baud=baud)

    # ── Connection lifecycle ──────────────────────────────────────────────────

    def connect(self) -> "GloveStream":
        """Open the connection. Called automatically when used as a context manager."""
        if self._use_zmq:
            self._connect_zmq()
        else:
            self._reader.start()
        return self

    def disconnect(self) -> None:
        """Close the connection."""
        if self._reader:
            self._reader.stop()
        if self._zmq_sock:
            try:
                self._zmq_sock.close()
            except Exception:
                pass
        if self._zmq_ctx:
            try:
                self._zmq_ctx.term()
            except Exception:
                pass
        self._zmq_sock = None
        self._zmq_ctx  = None

    def __enter__(self) -> "GloveStream":
        return self.connect()

    def __exit__(self, *_) -> None:
        self.disconnect()

    # ── Iteration ─────────────────────────────────────────────────────────────

    def __iter__(self) -> Iterator[GloveFrame]:
        if self._use_zmq:
            yield from self._iter_zmq()
        else:
            yield from self._iter_serial()

    def _iter_serial(self) -> Iterator[GloveFrame]:
        reader = self._reader
        if reader is None:
            raise RuntimeError("Not connected.")

        while True:
            # Surface any background thread errors (e.g. port disconnected)
            if reader._error is not None:
                raise reader._error

            try:
                raw = reader.queue.get(timeout=1.0)
            except Exception:
                if not reader._running:
                    if reader._error:
                        raise reader._error
                    return
                continue

            frame = _parse_frame(raw, ts=time.time())
            if frame is not None:
                yield frame

    def _iter_zmq(self) -> Iterator[GloveFrame]:
        import zmq
        sock = self._zmq_sock
        if sock is None:
            raise RuntimeError("Not connected.")

        while True:
            try:
                _topic, payload = sock.recv_multipart()
                msg   = json.loads(payload)
                frame = _parse_frame(msg.get("frame", {}), ts=msg.get("ts", time.time()))
                if frame is not None:
                    yield frame
            except KeyboardInterrupt:
                return
            except zmq.ZMQError as exc:
                if exc.errno == zmq.ETERM:
                    return
                raise

    # ── ZMQ setup ─────────────────────────────────────────────────────────────

    def _connect_zmq(self) -> None:
        try:
            import zmq
        except ImportError:
            raise ImportError(
                "pyzmq is required for ZMQ mode. Run:  pip install pyzmq"
            )
        self._zmq_ctx  = zmq.Context()
        self._zmq_sock = self._zmq_ctx.socket(zmq.SUB)
        self._zmq_sock.connect(f"tcp://{self._host}:{self._zmq_port}")
        self._zmq_sock.setsockopt(zmq.SUBSCRIBE, b"sensor")


# ── Internal parser ───────────────────────────────────────────────────────────

def _parse_frame(raw: dict, ts: float) -> Optional[GloveFrame]:
    if not raw:
        return None

    sensors: list[Sensor] = []

    for s in raw.get("sensors", []):
        stype = s.get("type")

        if stype == "angles":
            samples = [
                AnglesSample(ts_us=sa["ts_us"], angles_deg=sa["angles_deg"])
                for sa in s.get("samples", [])
            ]
            sensors.append(AnglesSensor(finger=s["finger"], com=s["com"], samples=samples))

        elif stype == "imu6":
            samples = [
                ImuSample(
                    ts_us=sa["ts_us"],
                    acc=tuple(sa["acc"]),    # type: ignore[arg-type]
                    gyro=tuple(sa["gyro"]),  # type: ignore[arg-type]
                )
                for sa in s.get("samples", [])
            ]
            sensors.append(ImuSensor(finger=s["finger"], com=s["com"], samples=samples))

        elif stype == "touch6":
            sensors.append(TouchSensor(
                finger=s["finger"],
                com=s["com"],
                ts_us=s["ts_us"],
                channels=s["channels"],
                channels_raw=s["channels_raw"],
            ))

    return GloveFrame(
        ts=ts,
        side=raw.get("side", ""),
        group=raw.get("group", ""),
        node_id=raw.get("node_id", 0),
        seq=raw.get("seq", 0),
        sensors=sensors,
    )
