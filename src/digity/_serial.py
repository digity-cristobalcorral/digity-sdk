"""
Serial reader — opens the ESP32 USB port, feeds raw bytes into the HUMI parser,
and puts decoded frames into a thread-safe queue.
"""

from __future__ import annotations

import queue
import threading
from typing import Optional

from . import _humi

BAUD_RATE   = 921600
BUFFER_MAX  = 8192   # drop oldest bytes if sync is lost beyond this
BUFFER_KEEP = 4096

# USB vendor IDs and description keywords for the ESP32/glove USB-serial chips
_VID_SET  = {"1A86", "10C4", "0403", "303A"}   # CH340, CP210x, FTDI, ESP32 built-in
_KEYWORDS = ("CH340", "CH341", "CP210", "FTDI", "ESP32", "USB SERIAL", "USB-SERIAL")


def find_glove_port() -> Optional[str]:
    """
    Scan connected serial ports and return the first one that looks like
    the glove's USB-serial chip (CH340 / CP210x / FTDI / ESP32 built-in).
    Returns None if nothing is found.
    """
    try:
        import serial.tools.list_ports
        for port in serial.tools.list_ports.comports():
            desc = f"{port.description or ''} {port.hwid or ''}".upper()
            if any(kw in desc for kw in _KEYWORDS):
                return port.device
            if any(vid in desc for vid in _VID_SET):
                return port.device
    except Exception:
        pass
    return None


class SerialReader:
    """
    Background thread that reads raw bytes from the glove serial port,
    parses HUMI frames, and puts GloveFrame-ready dicts into self.queue.
    """

    def __init__(self, port: Optional[str] = None, baud: int = BAUD_RATE) -> None:
        self.port  = port or find_glove_port()
        self.baud  = baud
        self.queue: queue.Queue[dict] = queue.Queue(maxsize=2000)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._error:  Optional[Exception] = None

    def start(self) -> None:
        if not self.port:
            raise GloveNotFoundError(
                "Digity glove not found. Make sure the USB cable is connected.\n"
                "If the port is not auto-detected, pass it explicitly:\n"
                "  GloveStream(port='/dev/ttyUSB0')   # Linux\n"
                "  GloveStream(port='COM3')            # Windows"
            )
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True, name="digity-serial")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        try:
            import serial
        except ImportError:
            self._error = ImportError(
                "pyserial is not installed. Run:  pip install digity"
            )
            return

        buf = b""
        try:
            with serial.Serial(self.port, self.baud, timeout=1.0) as ser:
                while self._running:
                    waiting = ser.in_waiting or 1
                    data    = ser.read(waiting)
                    if not data:
                        continue

                    buf += data
                    frames, buf = _humi.parse_stream(buf)

                    for frame in frames:
                        try:
                            self.queue.put_nowait(frame)
                        except queue.Full:
                            pass  # drop oldest by discarding the new one — keep stream live

                    if len(buf) > BUFFER_MAX:
                        buf = buf[-BUFFER_KEEP:]  # lost sync — trim buffer

        except Exception as exc:
            self._error = exc
            self._running = False


class GloveNotFoundError(RuntimeError):
    pass
