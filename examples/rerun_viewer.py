"""
Real-time Rerun viewer for the Digity sensorized exohand.

Renders the Inspire Hand 3D model (rigid GLB pieces) animated by live
forward-kinematics from glove angle data, plus per-finger charts.

Usage:
    python examples/rerun_viewer.py
    python examples/rerun_viewer.py /dev/ttyUSB0
    python examples/rerun_viewer.py COM3

Requirements:
    pip install rerun-sdk numpy
"""

import math
import pathlib
import site
import sys
from typing import Optional

# Guard: the PyPI package "rerun" (a CLI tool) shadows rerun-sdk.
try:
    import rerun as _rr_probe
    if not hasattr(_rr_probe, "log"):
        raise ImportError
except ImportError:
    for _d in site.getsitepackages():
        _sdk = pathlib.Path(_d) / "rerun_sdk"
        if _sdk.exists():
            sys.path.insert(0, str(_sdk))
            sys.modules.pop("rerun", None)
            break

import numpy as np
import rerun as rr

try:
    import rerun.blueprint as rrb
    _HAS_BLUEPRINT = True
except ImportError:
    _HAS_BLUEPRINT = False

from digity import GloveStream, AnglesSensor, ImuSensor, TouchSensor, GloveNotFoundError

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODELS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent
    / "src/digity/viz/static/models/inspire_hand"
)

# ---------------------------------------------------------------------------
# Kinematic chain  (ported from src/digity/viz/static/js/inspire_hand.js)
# ---------------------------------------------------------------------------

FINGER_NAMES = ["thumb", "index", "middle", "ring", "pinky"]

# [joint_name, parent_link, child_link, xyz_offset, rpy_ZYX, rotation_axis]
_JOINT_DEFS = [
    ("base_joint",                 "base",               "hand_base_link",      [ 0,       0,        0      ], [-1.5708,  0,       3.14159], [0, 0,  1]),
    ("thumb_proximal_yaw_joint",   "hand_base_link",     "thumb_proximal_base", [-0.01696,-0.0691,  -0.02045], [ 1.5708, -1.5708,  0      ], [0, 0, -1]),
    ("thumb_proximal_pitch_joint", "thumb_proximal_base","thumb_proximal",      [-0.0088099, 0.010892,-0.00925],[ 1.5708,  0,       2.8587 ], [0, 0,  1]),
    ("thumb_intermediate_joint",   "thumb_proximal",     "thumb_intermediate",  [ 0.04407, 0.034553,-0.0008  ], [ 0,       0,       0      ], [0, 0,  1]),
    ("thumb_distal_joint",         "thumb_intermediate", "thumb_distal",        [ 0.020248,0.010156,-0.0012  ], [ 0,       0,       0      ], [0, 0,  1]),
    ("index_proximal_joint",       "hand_base_link",     "index_proximal",      [ 0.00028533,-0.13653,-0.032268],[-3.1067, 0,       0      ], [0, 0,  1]),
    ("index_intermediate_joint",   "index_proximal",     "index_intermediate",  [-0.0026138, 0.032026,-0.001  ], [ 0,       0,       0      ], [0, 0,  1]),
    ("middle_proximal_joint",      "hand_base_link",     "middle_proximal",     [ 0.00028533,-0.1371, -0.01295], [-3.1416,  0,       0      ], [0, 0,  1]),
    ("middle_intermediate_joint",  "middle_proximal",    "middle_intermediate", [-0.0024229, 0.032041,-0.001  ], [ 0,       0,       0      ], [0, 0,  1]),
    ("ring_proximal_joint",        "hand_base_link",     "ring_proximal",       [ 0.00028533,-0.13691, 0.0062872],[ 3.0892, 0,       0      ], [0, 0,  1]),
    ("ring_intermediate_joint",    "ring_proximal",      "ring_intermediate",   [-0.0024229, 0.032041,-0.001  ], [ 0,       0,       0      ], [0, 0,  1]),
    ("pinky_proximal_joint",       "hand_base_link",     "pinky_proximal",      [ 0.00028533,-0.13571, 0.025488],[ 3.0369,  0,       0      ], [0, 0,  1]),
    ("pinky_intermediate_joint",   "pinky_proximal",     "pinky_intermediate",  [-0.0024229, 0.032041,-0.001  ], [ 0,       0,       0      ], [0, 0,  1]),
]

_LINK_VISUALS = [
    ("hand_base_link",     "right_base_link.glb"),
    ("thumb_proximal_base","right_thumb_proximal_base.glb"),
    ("thumb_proximal",     "right_thumb_proximal.glb"),
    ("thumb_intermediate", "right_thumb_intermediate.glb"),
    ("thumb_distal",       "right_thumb_distal.glb"),
    ("index_proximal",     "right_index_proximal.glb"),
    ("index_intermediate", "right_index_intermediate.glb"),
    ("middle_proximal",    "right_index_proximal.glb"),
    ("middle_intermediate","right_middle_intermediate.glb"),
    ("ring_proximal",      "right_index_proximal.glb"),
    ("ring_intermediate",  "right_index_intermediate.glb"),
    ("pinky_proximal",     "right_index_proximal.glb"),
    ("pinky_intermediate", "right_pinky_intermediate.glb"),
]

# Glove angle channels mapped to Inspire Hand joints per finger.
# Each tuple: (joint_name, angle_channel_index)
_FINGER_JOINTS = {
    0: [("thumb_proximal_yaw_joint",   3),   # abduction
        ("thumb_proximal_pitch_joint", 0),   # MCP flex
        ("thumb_intermediate_joint",   1),   # PIP
        ("thumb_distal_joint",         2)],  # DIP
    1: [("index_proximal_joint",       0),
        ("index_intermediate_joint",   1)],
    2: [("middle_proximal_joint",      0),
        ("middle_intermediate_joint",  1)],
    3: [("ring_proximal_joint",        0),
        ("ring_intermediate_joint",    1)],
    4: [("pinky_proximal_joint",       0),
        ("pinky_intermediate_joint",   1)],
}

# ---------------------------------------------------------------------------
# Hierarchy helpers
# ---------------------------------------------------------------------------

def _build_link_paths() -> dict:
    child_to_parent = {child: parent for _, parent, child, *_ in _JOINT_DEFS}

    def path_of(link: str) -> str:
        if link == "base":
            return "hand/base"
        return path_of(child_to_parent[link]) + "/" + link

    return {child: path_of(child) for _, _, child, *_ in _JOINT_DEFS}


_LINK_PATHS = _build_link_paths()

# ---------------------------------------------------------------------------
# Quaternion math  [x, y, z, w]
# ---------------------------------------------------------------------------

def _rpy_to_quat(r: float, p: float, y: float) -> np.ndarray:
    """ZYX Euler (Three.js convention) → quaternion [x, y, z, w]."""
    c1, s1 = math.cos(r / 2), math.sin(r / 2)
    c2, s2 = math.cos(p / 2), math.sin(p / 2)
    c3, s3 = math.cos(y / 2), math.sin(y / 2)
    return np.array([
        s1 * c2 * c3 - c1 * s2 * s3,
        c1 * s2 * c3 + s1 * c2 * s3,
        c1 * c2 * s3 - s1 * s2 * c3,
        c1 * c2 * c3 + s1 * s2 * s3,
    ])


def _quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ])


def _axis_angle_quat(axis: list, radians: float) -> np.ndarray:
    ax = np.array(axis, dtype=float)
    n = np.linalg.norm(ax)
    if n > 1e-9:
        ax /= n
    s, c = math.sin(radians / 2), math.cos(radians / 2)
    return np.array([ax[0] * s, ax[1] * s, ax[2] * s, c])


def _quat_to_mat3(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y*y + z*z),     2 * (x*y - w*z),     2 * (x*z + w*y)],
        [    2 * (x*y + w*z), 1 - 2 * (x*x + z*z),     2 * (y*z - w*x)],
        [    2 * (x*z - w*y),     2 * (y*z + w*x), 1 - 2 * (x*x + y*y)],
    ], dtype=float)


# Precompute rest quaternions for every joint
_REST_QUATS = {
    jname: _rpy_to_quat(*rpy)
    for jname, _, _, _, rpy, _ in _JOINT_DEFS
}

# ---------------------------------------------------------------------------
# Pose logging
# ---------------------------------------------------------------------------

def _log_pose(finger_angles: dict) -> None:
    joint_angles: dict = {}
    for fi, mappings in _FINGER_JOINTS.items():
        angles = finger_angles.get(fi, [])
        for jname, ch in mappings:
            joint_angles[jname] = math.radians(angles[ch]) if ch < len(angles) else 0.0

    for jname, _, child, xyz, _, axis in _JOINT_DEFS:
        angle = joint_angles.get(jname, 0.0)
        q = _quat_mul(_REST_QUATS[jname], _axis_angle_quat(axis, angle))
        rr.log(
            _LINK_PATHS[child],
            rr.Transform3D(
                translation=xyz,
                mat3x3=_quat_to_mat3(q).tolist(),
            ),
        )

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

_JOINT_CHANNEL_NAMES = ["MCP flex", "PIP flex", "DIP flex", "abduction", "aux"]
_FINGER_COLORS = [
    [255,  90,  90], [255, 185,  50],
    [ 60, 200,  60], [ 60, 160, 255], [185,  60, 255],
]


def _send_blueprint() -> None:
    if not _HAS_BLUEPRINT:
        return
    rr.send_blueprint(
        rrb.Blueprint(
            rrb.Horizontal(
                rrb.Spatial3DView(name="Hand 3D", origin="/"),
                rrb.Vertical(
                    rrb.Tabs(
                        *[rrb.TimeSeriesView(name=n.capitalize(), origin=f"/angles/{n}")
                          for n in FINGER_NAMES],
                        name="Angles per finger",
                    ),
                    rrb.Tabs(
                        rrb.TimeSeriesView(name="Touch", origin="/touch"),
                        rrb.TimeSeriesView(name="IMU",   origin="/imu"),
                        name="Other sensors",
                    ),
                    row_shares=[3, 1],
                ),
                column_shares=[3, 2],
            ),
            auto_views=False,
        )
    )

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def _setup_static() -> None:
    rr.log("/", rr.ViewCoordinates.RIGHT_HAND_Y_UP, static=True)

    # Rotate the whole hand -90° around X so fingers point up (+Y)
    rr.log(
        "hand",
        rr.Transform3D(
            rotation_axis_angle=rr.RotationAxisAngle(axis=[1, 0, 0], degrees=-90)
        ),
        static=True,
    )

    # Load each link's GLB mesh (static — never changes)
    for link_name, glb_file in _LINK_VISUALS:
        p = _MODELS_DIR / glb_file
        if p.exists():
            rr.log(f"{_LINK_PATHS[link_name]}/mesh", rr.Asset3D(path=str(p)), static=True)
        else:
            print(f"[warn] mesh not found: {p}")

    # Series line labels for angle charts
    for fi, name in enumerate(FINGER_NAMES):
        r, g, b = _FINGER_COLORS[fi]
        for ch in range(5):
            label = _JOINT_CHANNEL_NAMES[ch]
            bright = max(0.4, 1.0 - ch * 0.15)
            color = [int(r * bright), int(g * bright), int(b * bright)]
            rr.log(f"angles/{name}/joint_{ch}",
                   rr.SeriesLines(names=label, colors=[color]), static=True)

    # Rest pose at t=0 (non-static so live frames can override it)
    rr.set_time("wall_time", timestamp=0.0)
    _log_pose({})

# ---------------------------------------------------------------------------
# Per-frame
# ---------------------------------------------------------------------------

_live_angles: dict[int, list] = {}


def _log_angles(finger_idx: int, sensor: AnglesSensor) -> None:
    global _debug_frame
    angles = sensor.samples[-1].angles_deg
    name   = FINGER_NAMES[finger_idx]

    for i, deg in enumerate(angles):
        rr.log(f"angles/{name}/joint_{i}", rr.Scalars(deg))

    _live_angles[finger_idx] = list(angles)
    _log_pose(_live_angles)


def _log_imu(finger_idx: int, sensor: ImuSensor) -> None:
    name = FINGER_NAMES[finger_idx]
    last = sensor.samples[-1]
    for label, val in zip(
        ["acc_x", "acc_y", "acc_z", "gyro_x", "gyro_y", "gyro_z"],
        [*last.acc, *last.gyro],
    ):
        rr.log(f"imu/{name}/{label}", rr.Scalars(val))


def _log_touch(finger_idx: int, sensor: TouchSensor) -> None:
    name = FINGER_NAMES[finger_idx]
    for ch_idx, value in enumerate(sensor.channels):
        rr.log(f"touch/{name}/ch_{ch_idx}", rr.Scalars(value))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    port: Optional[str] = sys.argv[1] if len(sys.argv) > 1 else None

    rr.init("digity_glove", spawn=True)
    _send_blueprint()
    _setup_static()

    print("Rerun viewer launched — press Ctrl+C to stop")

    try:
        with GloveStream(port=port) as stream:
            for frame in stream:
                rr.set_time("wall_time", timestamp=frame.ts)
                for sensor in frame.sensors:
                    fi = sensor.finger
                    if fi >= len(FINGER_NAMES):
                        continue
                    if isinstance(sensor, AnglesSensor):
                        if frame.group == "hand":
                            _log_angles(fi, sensor)
                    elif isinstance(sensor, ImuSensor):
                        _log_imu(fi, sensor)
                    elif isinstance(sensor, TouchSensor):
                        _log_touch(fi, sensor)

    except GloveNotFoundError as e:
        print(e)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
