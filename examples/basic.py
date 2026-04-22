"""
Basic example — print every sensor frame from the exohand.

Just plug in the glove USB cable and run:
    python examples/basic.py

Explicit port (if auto-detection fails):
    python examples/basic.py /dev/ttyUSB0    # Linux
    python examples/basic.py COM3            # Windows
"""

import sys
from digity import GloveStream, AnglesSensor, ImuSensor, TouchSensor, GloveNotFoundError

port = sys.argv[1] if len(sys.argv) > 1 else None

try:
    with GloveStream(port=port) as stream:
        print("Glove connected — press Ctrl+C to stop\n")
        for frame in stream:
            print(f"[{frame.ts:.3f}]  {frame.side}/{frame.group}  node={frame.node_id}  seq={frame.seq}")

            for sensor in frame.sensors:
                if isinstance(sensor, AnglesSensor):
                    last = sensor.samples[-1]
                    degs = [round(d, 1) for d in last.angles_deg]
                    print(f"  angles  finger={sensor.finger}  {degs} deg")

                elif isinstance(sensor, ImuSensor):
                    last = sensor.samples[-1]
                    print(f"  imu     finger={sensor.finger}  acc={last.acc}  gyro={last.gyro}")

                elif isinstance(sensor, TouchSensor):
                    ch = [round(c, 2) for c in sensor.channels]
                    print(f"  touch   finger={sensor.finger}  channels={ch}")

except GloveNotFoundError as e:
    print(e)
    sys.exit(1)
