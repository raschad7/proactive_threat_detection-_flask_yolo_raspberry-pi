from datetime import datetime
from flask import Blueprint, render_template, session, request, redirect, url_for, Response, stream_with_context, jsonify
import requests, sqlite3
from website.utils import log_event, save_alert, get_alerts
import os
from werkzeug.utils import secure_filename
from flask import current_app
from website.utils import push_telegram
from flask import current_app, request, jsonify


views = Blueprint('views', __name__)

# Token used by Raspberry Pi to post alerts
API_TOKEN = "mysecret"  # Optional. Leave empty "" to disable token check.

# ──────────────────────────────────────────────
# ROOT → REDIRECT TO LOGIN
# ──────────────────────────────────────────────
@views.route('/')
def root():
    return redirect(url_for('auth.login_view'))

# ──────────────────────────────────────────────
# CAMERA MJPEG PROXY (from Pi)
# ──────────────────────────────────────────────
@views.route('/cam')
def camera_proxy():
    if 'user' not in session:
        return redirect(url_for('auth.login_view'))
    try:
        stream = requests.get("http://192.168.137.167:5000/video", stream=True, timeout=5)
        return Response(
            stream_with_context(stream.iter_content(chunk_size=1024)),
            content_type="multipart/x-mixed-replace; boundary=frame"
        )
    except requests.exceptions.RequestException:
        return "Camera feed unavailable", 503

# ──────────────────────────────────────────────
# PROTECTED PAGES
# ──────────────────────────────────────────────
@views.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('auth.login_view'))
    return render_template('dashboard.html')

@views.route('/alerts')
def alerts():
    if 'user' not in session:
        return redirect(url_for('auth.login_view'))
    return render_template('alerts.html')

@views.route('/gallery')
def gallery():
    if 'user' not in session:
        return redirect(url_for('auth.login_view'))
    return render_template('gallery.html')

@views.route('/logs')
def logs():
    if 'user' not in session:
        return redirect(url_for('auth.login_view'))
    conn = sqlite3.connect('logs.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    logs = c.fetchall()
    conn.close()
    return render_template('logs.html', logs=logs)

# ──────────────────────────────────────────────
# METRICS (called by dashboard every 5s)
# ──────────────────────────────────────────────
@views.route('/metrics')
def metrics():
    try:
        r = requests.get("http://192.168.1.111:5001/stats", timeout=1)
        pi_data = r.json()
    except Exception:
        pi_data = {"fps": None, "cpu_temp": None, "cpu_load": None, "ram": None}
    return jsonify({
        "fps": pi_data["fps"],
        "cpu_temp": pi_data["cpu_temp"],
        "cpu_load": pi_data["cpu_load"],
        "ram": pi_data["ram"],
        "pi_ping": None
    })

# ──────────────────────────────────────────────
# ALERT API (called by Pi)
# ──────────────────────────────────────────────

@views.route('/api/alert', methods=['POST'])
def api_alert():
    try:
        # ─── pull form fields ─────────────────────────────────────────
        label      = request.form.get("label")
        camera     = request.form.get("camera")
        conf_raw   = request.form.get("confidence")
        screenshot = request.files.get("screenshot")

        # ─── validate confidence ─────────────────────────────────────
        try:
            confidence = float(conf_raw)
        except (TypeError, ValueError):
            print("[ERROR] Invalid confidence:", conf_raw)
            return jsonify({"error": "Invalid confidence"}), 400

        # ─── save screenshot (if provided) ────────────────────────────
        filename  = None
        img_path  = None
        if screenshot and screenshot.filename:
            ts         = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_label = secure_filename(label or "alert")
            filename   = f"{ts}_{safe_label}.jpg"

            save_dir = os.path.join(current_app.root_path, "static", "screens")
            os.makedirs(save_dir, exist_ok=True)
            img_path = os.path.join(save_dir, filename)
            screenshot.save(img_path)
            print("[DEBUG] Screenshot saved ->", img_path)

        # ─── insert alert into SQLite ────────────────────────────────
        conn = sqlite3.connect("alerts.db")
        cur  = conn.cursor()
        cur.execute(
            '''
            INSERT INTO alerts (timestamp, camera, label, confidence, status, image)
            VALUES (?, ?, ?, ?, 'unread', ?)
            ''',
            (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                camera,
                label,
                int(confidence),
                filename
            )
        )
        conn.commit()
        conn.close()

        # ─── push Telegram notification  (non-blocking) ──────────────
        msg = f"🚨 {label} detected\nCam: {camera}\nConf: {confidence:.1f}%"
        push_telegram(msg, img_path)         # sends with photo if it exists

        print(f"[ALERT STORED] {label} {confidence:.1f}% — img: {filename or 'none'}")
        return jsonify({"status": "stored"}), 201

    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────
# ALERT LIST API (called by dashboard JS poller)
# ──────────────────────────────────────────────
@views.route('/api/alert/list')
def api_alert_list():
    if 'user' not in session:
        return jsonify({"error": "auth"}), 403
    return jsonify(get_alerts(200))  # adjust count as needed


@views.route('/api/alert/bulk', methods=['POST'])
def api_alert_bulk():
    if 'user' not in session:
        return jsonify({"error": "unauthorized"}), 403

    data = request.get_json()
    ids = data.get("ids", [])
    action = data.get("action")

    if not ids or action not in ["read", "unread", "delete"]:
        return jsonify({"error": "Invalid input"}), 400

    conn = sqlite3.connect('alerts.db')
    c = conn.cursor()

    if action in ["read", "unread"]:
        c.execute(
            f"UPDATE alerts SET status = ? WHERE id IN ({','.join(['?']*len(ids))})",
            [action] + ids
        )
    elif action == "delete":
        c.execute(
            f"DELETE FROM alerts WHERE id IN ({','.join(['?']*len(ids))})",
            ids
        )

    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "affected": len(ids)})