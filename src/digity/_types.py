"""
Data types returned by GloveStream.

Each frame yielded by GloveStream is a GloveFrame containing a list of
sensors. Each sensor is one of AnglesSensor, ImuSensor, or TouchSensor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass
class AnglesSample:
    """One timestamped angle reading from a single sensor node."""
    ts_us: int              # microsecond timestamp from the sensor
    angles_deg: list[float] # joint angles in degrees (number varies by node)


@dataclass
class ImuSample:
    """One timestamped IMU reading (accelerometer + gyroscope)."""
    ts_us: int                      # microsecond timestamp from the sensor
    acc: tuple[int, int, int]       # accelerometer (x, y, z), raw i16
    gyro: tuple[int, int, int]      # gyroscope    (x, y, z), raw i16


@dataclass
class AnglesSensor:
    """Angle sensor attached to a finger node."""
    finger: int                  # finger index (0-based)
    com: int                     # communication line index
    samples: list[AnglesSample]  # one or more samples in this frame


@dataclass
class ImuSensor:
    """IMU sensor (6-axis) attached to a finger node."""
    finger: int
    com: int
    samples: list[ImuSample]


@dataclass
class TouchSensor:
    """6-channel capacitive touch sensor."""
    finger: int
    com: int
    ts_us: int
    channels: list[float]      # 6 values, normalised 0.0 .. 1.0
    channels_raw: list[int]    # 6 values, raw ADC counts 0 .. 4095


Sensor = Union[AnglesSensor, ImuSensor, TouchSensor]


@dataclass
class GloveFrame:
    """
    One decoded sensor frame from the glove.

    Attributes:
        ts        Host timestamp (seconds since epoch) when the frame arrived.
        side      "right" or "left".
        group     "hand" or "arm".
        node_id   Integer node identifier on the glove PCB.
        seq       Packet sequence number (wraps at 65535).
        sensors   List of sensor readings in this frame. Each element is an
                  AnglesSensor, ImuSensor, or TouchSensor instance.
    """
    ts: float
    side: str
    group: str
    node_id: int
    seq: int
    sensors: list[Sensor]
