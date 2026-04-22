"""Stream local glove data to a remote digity-viz server."""

import sys
import time


_RETRY_DELAY = 5


def _frame_to_dict(frame) -> dict:
    from .. import AnglesSensor, ImuSensor, TouchSensor

    sensors = []
    for s in frame.sensors:
        if isinstance(s, AnglesSensor):
            sensors.append({
                "type": "angles", "finger": s.finger, "com": s.com,
                "samples": [{"ts_us": sa.ts_us, "angles_deg": sa.angles_deg} for sa in s.samples],
            })
        elif isinstance(s, ImuSensor):
            sensors.append({
                "type": "imu6", "finger": s.finger, "com": s.com,
                "samples": [{"ts_us": sa.ts_us, "acc": list(sa.acc), "gyro": list(sa.gyro)}
                            for sa in s.samples],
            })
        elif isinstance(s, TouchSensor):
            sensors.append({
                "type": "touch6", "finger": s.finger, "com": s.com,
                "ts_us": s.ts_us, "channels": s.channels, "channels_raw": s.channels_raw,
            })
    return {
        "type": "sensor_frame",
        "ts": frame.ts,
        "frame": {
            "side": frame.side, "group": frame.group,
            "node_id": frame.node_id, "seq": frame.seq,
            "sensors": sensors,
        },
    }


def run(token: str, url: str = "https://app.digity.de/chiros", port=None):
    """Stream glove data to a remote digity-viz server. Blocks and retries on disconnect."""
    try:
        import socketio as _sio_mod
    except ImportError:
        print("Missing dependency — install with:  pip install 'digity[agent]'")
        sys.exit(1)

    from urllib.parse import urlparse
    from .. import GloveStream, GloveNotFoundError

    parsed = urlparse(url.rstrip("/"))
    base_path = parsed.path or ""
    server_root = f"{parsed.scheme}://{parsed.netloc}"
    socketio_path = base_path + "/socket.io"

    print(f"[digity-agent] server : {url}")
    print(f"[digity-agent] token  : …{token[-4:]}")
    print(f"[digity-agent] glove  : {port or 'auto-detect'}")

    while True:
        sio = _sio_mod.Client(reconnection=False, logger=False, engineio_logger=False)
        connected = False

        @sio.event(namespace="/agent")
        def connect():
            nonlocal connected
            connected = True
            print("[digity-agent] connected to server")

        @sio.event(namespace="/agent")
        def disconnect():
            nonlocal connected
            connected = False

        try:
            sio.connect(
                server_root,
                namespaces=["/agent"],
                socketio_path=socketio_path,
                auth={"token": token},
                transports=["websocket"],
                wait_timeout=10,
            )
        except Exception as exc:
            print(f"[digity-agent] cannot reach server: {exc}")
            time.sleep(_RETRY_DELAY)
            continue

        try:
            print(f"[digity-agent] scanning for glove on {port or 'auto'} …")
            with GloveStream(port=port) as stream:
                print("[digity-agent] glove connected — streaming")
                for frame in stream:
                    if not connected:
                        break
                    sio.emit("frame", _frame_to_dict(frame), namespace="/agent")
        except GloveNotFoundError as exc:
            print(f"[digity-agent] glove not found: {exc}")
        except Exception as exc:
            print(f"[digity-agent] error: {exc}")
        finally:
            try:
                sio.disconnect()
            except Exception:
                pass

        print(f"[digity-agent] retrying in {_RETRY_DELAY}s …")
        time.sleep(_RETRY_DELAY)
