"""
digity — Python SDK for the Digity sensorized exohand.

Install:
    pip install digity

Quick start:
    from digity import GloveStream, AnglesSensor

    with GloveStream() as stream:          # auto-detects USB port
        for frame in stream:
            for sensor in frame.sensors:
                if isinstance(sensor, AnglesSensor):
                    print(sensor.finger, sensor.samples[-1].angles_deg)
"""

from ._publisher import GlovePublisher
from ._serial import GloveNotFoundError
from ._stream import GloveStream
from ._types import (
    AnglesSample,
    AnglesSensor,
    GloveFrame,
    ImuSample,
    ImuSensor,
    Sensor,
    TouchSensor,
)

__version__ = "0.2.3"

__all__ = [
    "GloveStream",
    "GlovePublisher",
    "GloveNotFoundError",
    "GloveFrame",
    "AnglesSensor",
    "AnglesSample",
    "ImuSensor",
    "ImuSample",
    "TouchSensor",
    "Sensor",
]
