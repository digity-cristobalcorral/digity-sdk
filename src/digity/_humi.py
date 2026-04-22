"""
HUMI binary protocol parser.

Decodes raw bytes coming from the ESP32 glove into structured frames.
Packet format (little-endian):

  Header (9 bytes):
    [pkt_type:u8, ver:u8, side:u8, group:u8, node_id:u8, seq:u16, payload_len:u16]

  Payload:
    [n_sens:u8] + sensor records

Sensor records:
  ANGLES_N (0x10): joint angles in centidegrees
  IMU6     (0x11): 6-axis IMU (accel + gyro)
  TOUCH6   (0x12): 6-channel capacitive touch
"""

from __future__ import annotations

import struct
from typing import Optional

HEADER_SIZE      = 9
PKT_TYPE_DATA    = 0x01
PROTOCOL_VERSION = 0x02

SENS_ANGLES = 0x10
SENS_IMU6   = 0x11
SENS_TOUCH6 = 0x12

GROUP_ARM  = 0
GROUP_HAND = 1

_N_ANGLES_TABLE: dict[tuple[int, int], int] = {
    (GROUP_ARM, 1): 3,
    (GROUP_ARM, 2): 2,
    (GROUP_ARM, 3): 2,
    (GROUP_ARM, 4): 3,
}

def _n_angles(group: int, node_id: int) -> int:
    if group == GROUP_HAND:
        return 5
    return _N_ANGLES_TABLE.get((group, node_id), 3)


def parse_stream(buf: bytes) -> tuple[list[dict], bytes]:
    """
    Parse as many complete HUMI packets as possible from buf.
    Returns (frames, remaining_bytes).
    """
    frames: list[dict] = []
    i = 0
    n = len(buf)

    while i <= n - HEADER_SIZE:
        if buf[i] != PKT_TYPE_DATA or buf[i + 1] != PROTOCOL_VERSION:
            i += 1
            continue

        try:
            _, _, side, grp, nid, seq, payload_len = struct.unpack_from("<5BHH", buf, i)
        except struct.error:
            i += 1
            continue

        if payload_len > 4096:
            i += 1
            continue

        total = HEADER_SIZE + payload_len
        if i + total > n:
            break  # incomplete — wait for more bytes

        payload = buf[i + HEADER_SIZE: i + total]
        try:
            frame = _parse_payload(payload, side, grp, nid, seq)
        except Exception:
            i += total
            continue
        if frame is not None:
            frames.append(frame)

        i += total

    return frames, buf[i:]


def _parse_payload(payload: bytes, side: int, group: int, node_id: int, seq: int) -> Optional[dict]:
    if not payload:
        return None

    n_sens = payload[0]
    pos    = 1
    sensors: list[dict] = []

    for _ in range(n_sens):
        if pos >= len(payload):
            break
        rec, consumed = _parse_record(payload, pos, group, node_id)
        if rec is None or consumed == 0:
            break
        sensors.append(rec)
        pos += consumed

    return {
        "side":    "right" if side == 0 else "left",
        "group":   "arm"   if group == GROUP_ARM else "hand",
        "node_id": node_id,
        "seq":     seq,
        "sensors": sensors,
    }


def _parse_record(data: bytes, pos: int, group: int, node_id: int) -> tuple[Optional[dict], int]:
    if pos + 3 > len(data):
        return None, 0

    sens_type  = data[pos]
    sens_id    = data[pos + 1]
    n_samples  = data[pos + 2]
    finger_idx = (sens_id >> 4) & 0x0F
    com_line   = sens_id & 0x0F
    p          = pos + 3

    if sens_type == SENS_ANGLES:
        if p + 10 > len(data):
            return None, 0
        t0_us, dt_us = struct.unpack_from("<QH", data, p)
        p += 10

        na           = _n_angles(group, node_id)
        sample_bytes = na * 2
        if p + n_samples * sample_bytes > len(data):
            return None, 0

        samples = []
        for k in range(n_samples):
            raw = struct.unpack_from(f"<{na}h", data, p)
            samples.append({
                "ts_us":      t0_us + k * dt_us,
                "angles_deg": [v / 100.0 for v in raw],
            })
            p += sample_bytes

        record = {
            "type": "angles", "finger": finger_idx, "com": com_line, "n": na, "samples": samples
        }
        return record, p - pos

    if sens_type == SENS_IMU6:
        if p + 14 > len(data):
            return None, 0
        t0_us = struct.unpack_from("<Q", data, p)[0]
        dt_us = struct.unpack_from("<H", data, p + 8)[0]
        p += 14

        sample_bytes = 12
        if p + n_samples * sample_bytes > len(data):
            return None, 0

        samples = []
        for k in range(n_samples):
            ax, ay, az, gx, gy, gz = struct.unpack_from("<6h", data, p)
            samples.append({"ts_us": t0_us + k * dt_us, "acc": [ax, ay, az], "gyro": [gx, gy, gz]})
            p += sample_bytes

        return {"type": "imu6", "finger": finger_idx, "com": com_line, "samples": samples}, p - pos

    if sens_type == SENS_TOUCH6:
        if p + 20 > len(data):
            return None, 0
        t0_us    = struct.unpack_from("<Q", data, p)[0]
        channels = list(struct.unpack_from("<6H", data, p + 8))
        p += 20

        return {
            "type":         "touch6",
            "finger":       finger_idx,
            "com":          com_line,
            "ts_us":        t0_us,
            "channels":     [c / 4095.0 for c in channels],
            "channels_raw": channels,
        }, p - pos

    return None, 0
