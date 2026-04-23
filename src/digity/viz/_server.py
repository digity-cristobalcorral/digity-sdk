"""
digity.viz._server — Flask + SocketIO server for the digity dashboard.

Not meant to be imported directly — use digity.viz.start() or the digity-viz CLI.
"""

import json
import os
import secrets
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file
from flask_login import (
    LoginManager, UserMixin,
    current_user, login_required, login_user,
)
from flask_socketio import SocketIO, join_room
from werkzeug.security import generate_password_hash
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound as _NotFound

from .. import (
    AnglesSensor,
    GloveNotFoundError,
    GlovePublisher,
    GloveStream,
    ImuSensor,
    TouchSensor,
)

# ── Paths ──────────────────────────────────────────────────────────────────────

_BASE_DIR = Path(__file__).parent          # src/digity/viz/
_DATA_DIR = Path.home() / ".digity"       # ~/.digity/ — mutable user data
_DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH  = _DATA_DIR / "viz.db"
KEY_PATH = _DATA_DIR / "viz.key"

CONFIG_PATH = _DATA_DIR / "config.json"
TASKS_PATH  = _DATA_DIR / "tasks.json"

APP_PREFIX = "/chiros"

# ── App ────────────────────────────────────────────────────────────────────────

app = Flask(
    __name__,
    template_folder=str(_BASE_DIR / "templates"),
    static_folder=str(_BASE_DIR / "static"),
)

if KEY_PATH.exists():
    app.secret_key = KEY_PATH.read_text().strip()
else:
    _sk = secrets.token_hex(32)
    KEY_PATH.write_text(_sk)
    app.secret_key = _sk

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Always mount at /chiros so templates work without modification
app.wsgi_app = DispatcherMiddleware(_NotFound(), {"/chiros": app.wsgi_app})

# ── Config / Tasks ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "station_name":   "Station 1",
    "serial_port":    "",
    "baud_rate":      921600,
    "recordings_dir": str(Path.home() / "digity-recordings"),
}

DEFAULT_TASKS = ["grasp", "pinch", "point", "rest", "wave"]


def _load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except Exception:
            pass
    return cfg


def _save_config(data: dict):
    cfg = _load_config()
    cfg.update(data)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


def _load_tasks() -> list:
    if TASKS_PATH.exists():
        try:
            return json.loads(TASKS_PATH.read_text())
        except Exception:
            pass
    return list(DEFAULT_TASKS)


def _save_tasks(tasks: list):
    TASKS_PATH.write_text(json.dumps(tasks))


# ── Database ───────────────────────────────────────────────────────────────────

def _init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                is_admin      INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_tokens (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token   TEXT    UNIQUE NOT NULL
            )
        """)
        row = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
        if not row:
            conn.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?,?,1)",
                ("local", generate_password_hash(secrets.token_hex(16))),
            )
        conn.commit()


def _db_get_user_by_id(user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def _db_get_or_create_token(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT token FROM agent_tokens WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return row[0]
        token = secrets.token_hex(16)
        conn.execute(
            "INSERT INTO agent_tokens (user_id, token) VALUES (?,?)", (user_id, token)
        )
        conn.commit()
        return token


def _db_regenerate_token(user_id: int) -> str:
    token = secrets.token_hex(16)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM agent_tokens WHERE user_id=?", (user_id,))
        conn.execute(
            "INSERT INTO agent_tokens (user_id, token) VALUES (?,?)", (user_id, token)
        )
        conn.commit()
    return token


def _db_get_user_id_by_token(token: str):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT user_id FROM agent_tokens WHERE token=?", (token,)
        ).fetchone()
        return row[0] if row else None


# ── Flask-Login ────────────────────────────────────────────────────────────────

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, id: int, username: str, is_admin: bool = True):
        self.id       = id
        self.username = username
        self.is_admin = bool(is_admin)


@login_manager.user_loader
def load_user(user_id: str):
    row = _db_get_user_by_id(int(user_id))
    return User(row["id"], row["username"]) if row else None


@app.context_processor
def _inject_globals():
    return {"is_local": True}


@app.before_request
def _auto_login():
    if request.path.startswith("/static") or request.path.startswith("/socket.io"):
        return
    if not current_user.is_authenticated:
        row = _db_get_user_by_id(1)
        if row:
            login_user(User(row["id"], row["username"]), remember=True)


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/"):
        return jsonify({"error": "unauthorized"}), 401
    return redirect(f"{APP_PREFIX}/")


# ── Recording state ────────────────────────────────────────────────────────────

_rec_lock = threading.Lock()
_rec: dict = {
    "active":        False,
    "session_id":    None,
    "meta":          {},
    "start_ts":      None,
    "frame_count":   0,
    "bytes_written": 0,
    "user_id":       None,
    "_file":         None,
    "_dir":          None,
}

# ── Glove telemetry state ──────────────────────────────────────────────────────

_glove: dict = {
    "connected": False,
    "port":      None,
    "hz":        0.0,
}

_publisher  = GlovePublisher()
_hz_frames  = 0
_hz_last    = time.time()

# ── Agent relay sessions ───────────────────────────────────────────────────────

_agent_sessions: dict = {}

# ── Frame serialization ────────────────────────────────────────────────────────

def _frame_to_dict(frame) -> dict:
    sensors = []
    for s in frame.sensors:
        if isinstance(s, AnglesSensor):
            sensors.append({
                "type":    "angles",
                "finger":  s.finger,
                "com":     s.com,
                "samples": [
                    {"ts_us": sa.ts_us, "angles_deg": sa.angles_deg}
                    for sa in s.samples
                ],
            })
        elif isinstance(s, ImuSensor):
            sensors.append({
                "type":    "imu6",
                "finger":  s.finger,
                "com":     s.com,
                "samples": [
                    {"ts_us": sa.ts_us, "acc": list(sa.acc), "gyro": list(sa.gyro)}
                    for sa in s.samples
                ],
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
    return {
        "type": "sensor_frame",
        "ts":   frame.ts,
        "frame": {
            "side":    frame.side,
            "group":   frame.group,
            "node_id": frame.node_id,
            "seq":     frame.seq,
            "sensors": sensors,
        },
    }


# ── Glove stream thread ────────────────────────────────────────────────────────

def _stream_glove(port=None):
    global _hz_frames, _hz_last

    _hz_frames = 0
    _hz_last   = time.time()

    try:
        with GloveStream(port=port) as stream:
            _glove["connected"] = True
            _glove["port"]      = port or "auto"
            socketio.emit("glove_telemetry", {"connected": True, "port": _glove["port"]})

            for frame in stream:
                _publisher.publish(frame)
                data = _frame_to_dict(frame)
                socketio.emit("hand_frame", data)

                _hz_frames += 1
                now = time.time()
                dt  = now - _hz_last
                if dt >= 1.0:
                    _glove["hz"] = _hz_frames / dt
                    _hz_frames   = 0
                    _hz_last     = now
                    with _rec_lock:
                        socketio.emit("glove_telemetry", {
                            "connected":   True,
                            "port":        _glove["port"],
                            "hz":          round(_glove["hz"], 1),
                            "recording":   _rec["active"],
                            "frame_count": _rec["frame_count"],
                            "session_id":  _rec["session_id"],
                            "duration":    (now - _rec["start_ts"]) if _rec["active"] else 0,
                        })

                with _rec_lock:
                    if _rec["active"] and _rec["_file"]:
                        try:
                            line = json.dumps({"ts": data["ts"], **data["frame"]}) + "\n"
                            _rec["_file"].write(line)
                            _rec["frame_count"] += 1
                            _rec["bytes_written"] += len(line.encode())
                        except Exception:
                            pass

    except GloveNotFoundError as exc:
        socketio.emit("glove_telemetry", {"connected": False, "error": str(exc)})
    except Exception as exc:
        socketio.emit("glove_telemetry", {"connected": False, "error": str(exc)})
    finally:
        _glove["connected"] = False
        _glove["hz"]        = 0.0
        with _rec_lock:
            if _rec["active"] and _rec["_file"]:
                try:
                    _rec["_file"].close()
                except Exception:
                    pass
                _rec["_file"]   = None
                _rec["active"]  = False
                _rec["user_id"] = None
                socketio.emit("recording_state", {
                    "recording":  False,
                    "reason":     "glove_disconnected",
                    "session_id": _rec["session_id"],
                })


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login_page():
    return redirect(f"{APP_PREFIX}/")


@app.route("/logout")
def logout():
    return redirect(f"{APP_PREFIX}/")


# ── Browser Socket.IO ──────────────────────────────────────────────────────────

@socketio.on("connect")
def browser_connect():
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")


# ── Page routes ────────────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("viewer.html", username="")


@app.route("/record")
@login_required
def record_page():
    return render_template("record.html", username="")


@app.route("/setup")
@login_required
def setup_page():
    return render_template("setup.html", username="")


@app.route("/multiview")
@login_required
def multiview_page():
    return render_template("multiview.html", username="")


# ── Recording API ──────────────────────────────────────────────────────────────

@app.route("/api/record/start", methods=["POST"])
@login_required
def api_record_start():
    body    = request.json or {}
    cfg     = _load_config()
    now_utc = datetime.now(timezone.utc)

    subject = (body.get("user_id") or "user").strip()
    task    = (body.get("task")    or "task").strip()
    hand    = (body.get("hand")    or "right").strip()
    notes   = (body.get("notes")   or "").strip()

    session_id  = f"{subject}_{task}_{now_utc.strftime('%Y-%m-%dT%H-%M-%S')}"
    rec_base    = Path(cfg.get("recordings_dir", str(Path.home() / "digity-recordings")))
    session_dir = rec_base / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "session_id":    session_id,
        "user_id":       subject,
        "task":          task,
        "hand":          hand,
        "station":       cfg.get("station_name", ""),
        "notes":         notes,
        "host_ts_start": time.time(),
    }
    (session_dir / "meta.json").write_text(json.dumps(meta, indent=2))

    with _rec_lock:
        if _rec["active"]:
            return jsonify({"ok": False, "error": "already recording"}), 409
        _rec["active"]        = True
        _rec["session_id"]    = session_id
        _rec["meta"]          = meta
        _rec["start_ts"]      = meta["host_ts_start"]
        _rec["frame_count"]   = 0
        _rec["bytes_written"] = 0
        _rec["user_id"]       = 1
        _rec["_dir"]          = str(session_dir)
        _rec["_file"]         = open(session_dir / "recording.jsonl", "w", buffering=1)

    socketio.emit("recording_state", {"recording": True, "session_id": session_id, "meta": meta})
    return jsonify({"ok": True, "session_id": session_id})


@app.route("/api/record/stop", methods=["POST"])
@login_required
def api_record_stop():
    with _rec_lock:
        if not _rec["active"]:
            return jsonify({"ok": False, "error": "not recording"}), 400

        end_ts        = time.time()
        session_id    = _rec["session_id"]
        frame_count   = _rec["frame_count"]
        bytes_written = _rec["bytes_written"]

        if _rec["_file"]:
            try:
                _rec["_file"].close()
            except Exception:
                pass
            _rec["_file"] = None

        if _rec["_dir"]:
            meta = dict(_rec["meta"])
            meta["host_ts_end"]   = end_ts
            meta["duration_s"]    = round(end_ts - _rec["start_ts"], 3)
            meta["frame_count"]   = frame_count
            meta["bytes_written"] = bytes_written
            try:
                (Path(_rec["_dir"]) / "meta.json").write_text(json.dumps(meta, indent=2))
            except Exception:
                pass

        _rec["active"]     = False
        _rec["session_id"] = None
        _rec["start_ts"]   = None
        _rec["user_id"]    = None

    socketio.emit("recording_state", {
        "recording":   False,
        "session_id":  session_id,
        "frame_count": frame_count,
    })
    return jsonify({"ok": True, "session_id": session_id, "frame_count": frame_count})


@app.route("/api/record/status")
@login_required
def api_record_status():
    with _rec_lock:
        return jsonify({
            "recording":   _rec["active"],
            "session_id":  _rec["session_id"],
            "frame_count": _rec["frame_count"],
            "duration":    (time.time() - _rec["start_ts"]) if _rec["active"] else 0,
        })


# ── Sessions API ───────────────────────────────────────────────────────────────

@app.route("/api/sessions")
@login_required
def api_sessions():
    cfg      = _load_config()
    rec_base = Path(cfg.get("recordings_dir", str(Path.home() / "digity-recordings")))
    sessions = []
    if rec_base.exists():
        for d in sorted(rec_base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not d.is_dir():
                continue
            meta_path = d / "meta.json"
            rec_path  = d / "recording.jsonl"
            meta = {}
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                except Exception:
                    pass
            sessions.append({
                "name":       d.name,
                "meta":       meta,
                "size_bytes": rec_path.stat().st_size if rec_path.exists() else 0,
                "mtime":      d.stat().st_mtime,
            })
    return jsonify(sessions)


@app.route("/api/sessions/<path:name>/download")
@login_required
def api_session_download(name):
    cfg      = _load_config()
    rec_base = Path(cfg.get("recordings_dir", str(Path.home() / "digity-recordings")))
    rec_file = rec_base / name / "recording.jsonl"
    if not rec_file.exists():
        return "Not found", 404
    return send_file(str(rec_file.resolve()), as_attachment=True,
                     download_name=f"{name}.jsonl")


@app.route("/api/sessions/<path:name>", methods=["DELETE"])
@login_required
def api_session_delete(name):
    cfg         = _load_config()
    rec_base    = Path(cfg.get("recordings_dir", str(Path.home() / "digity-recordings")))
    session_dir = rec_base / name
    if not session_dir.exists() or not session_dir.is_dir():
        return jsonify({"ok": False, "error": "not found"}), 404
    try:
        session_dir.resolve().relative_to(rec_base.resolve())
    except ValueError:
        return jsonify({"ok": False, "error": "forbidden"}), 403
    shutil.rmtree(str(session_dir))
    return jsonify({"ok": True})


# ── Config API ─────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
@login_required
def api_config_get():
    return jsonify(_load_config())


@app.route("/api/config", methods=["POST"])
@login_required
def api_config_set():
    _save_config(request.json or {})
    return jsonify({"ok": True})


# ── Tasks API ──────────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
@login_required
def api_tasks_get():
    return jsonify(_load_tasks())


@app.route("/api/tasks", methods=["POST"])
@login_required
def api_tasks_post():
    name = ((request.json or {}).get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "empty name"}), 400
    tasks = _load_tasks()
    if name not in tasks:
        tasks.append(name)
        _save_tasks(tasks)
    return jsonify({"ok": True, "tasks": tasks})


@app.route("/api/tasks/<name>", methods=["DELETE"])
@login_required
def api_tasks_delete(name):
    tasks = [t for t in _load_tasks() if t != name]
    _save_tasks(tasks)
    return jsonify({"ok": True, "tasks": tasks})


# ── Agent token API ────────────────────────────────────────────────────────────

@app.route("/api/agent/token", methods=["GET"])
@login_required
def api_agent_token_get():
    token = _db_get_or_create_token(current_user.id)
    return jsonify({"token": token})


@app.route("/api/agent/token/regenerate", methods=["POST"])
@login_required
def api_agent_token_regenerate():
    token = _db_regenerate_token(current_user.id)
    return jsonify({"token": token})


@app.route("/api/agent/exe-available")
@login_required
def api_agent_exe_available():
    return jsonify({"available": False})


@app.route("/api/server/exe-available")
@login_required
def api_server_exe_available():
    return jsonify({"available": False})


# ── Agent relay (remote glove PC → browser) ───────────────────────────────────

@socketio.on("connect", namespace="/agent")
def agent_connect(auth):
    token = ""
    if isinstance(auth, dict):
        token = auth.get("token", "")
    if not token:
        token = request.args.get("token", "")

    user_id = _db_get_user_id_by_token(token)
    if not user_id:
        return False

    _agent_sessions[request.sid] = user_id
    join_room(f"user_{user_id}", namespace="/agent")


@socketio.on("disconnect", namespace="/agent")
def agent_disconnect():
    _agent_sessions.pop(request.sid, None)


@socketio.on("frame", namespace="/agent")
def agent_frame(data):
    user_id = _agent_sessions.get(request.sid)
    if user_id:
        socketio.emit("hand_frame", data, room=f"user_{user_id}")


# ── Update check API ──────────────────────────────────────────────────────────

@app.route("/api/check-update")
@login_required
def api_check_update():
    import urllib.request
    from digity import __version__ as current

    def _vtuple(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except Exception:
            return (0,)

    try:
        with urllib.request.urlopen("https://pypi.org/pypi/digity/json", timeout=5) as resp:
            data = json.loads(resp.read())
        latest = data["info"]["version"]
        return jsonify({"current": current, "latest": latest,
                        "has_update": _vtuple(latest) > _vtuple(current)})
    except Exception as exc:
        return jsonify({"current": current, "error": str(exc)})


# ── Status API ─────────────────────────────────────────────────────────────────

@app.route("/api/status")
@login_required
def api_status():
    import sys as _sys
    from digity import __version__ as sdk_ver
    with _rec_lock:
        rec_active = _rec["active"]
        session_id = _rec["session_id"]
    return jsonify({
        "glove_connected": _glove["connected"],
        "glove_port":      _glove["port"],
        "glove_hz":        round(_glove["hz"], 1),
        "recording":       rec_active,
        "session_id":      session_id,
        "sdk_version":     sdk_ver,
        "python_version":  _sys.version.split()[0],
    })


# ── Public entry point ─────────────────────────────────────────────────────────

def run(port=None, desktop=True):
    """Start the digity visualizer. Blocks until the window is closed."""
    _init_db()
    _publisher.start()

    t = threading.Thread(target=_stream_glove, args=(port,), daemon=True)
    t.start()

    def _run_flask():
        socketio.run(app, host="127.0.0.1", port=5001, debug=False,
                     allow_unsafe_werkzeug=True)

    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    import urllib.request
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:5001/chiros/", timeout=1)
            break
        except Exception:
            time.sleep(0.3)

    if desktop:
        try:
            import webview
            webview.create_window(
                "digity viz",
                "http://127.0.0.1:5001/chiros/",
                width=1400, height=900,
                min_size=(900, 600),
            )
            webview.start()
            return
        except Exception:
            pass  # no GUI toolkit available — fall back to browser

    import webbrowser
    print("Open http://127.0.0.1:5001/chiros/ in your browser")
    webbrowser.open("http://127.0.0.1:5001/chiros/")
    flask_thread.join()
