import sqlite3, os, requests
from datetime import datetime

# ────────────────────────────
# Paths (adjust if needed)
# ────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DB    = os.path.join(BASE_DIR, "..", "logs.db")
ALERT_DB  = os.path.join(BASE_DIR, "..", "alerts.db")

# ────────────────────────────
# Logging System Events
# ────────────────────────────
def log_event(category: str, message: str):
    """Insert a log row into logs.db"""
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO logs (timestamp, category, message) VALUES (?, ?, ?)",
            (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                category,
                message
            )
        )
        conn.commit()
    finally:
        conn.close()

# ────────────────────────────
# Saving New Alerts
# ────────────────────────────
def save_alert(camera: str, label: str, confidence: float, image=None):
    """Insert a new alert row into alerts.db"""
    try:
        conn = sqlite3.connect(ALERT_DB)
        c = conn.cursor()
        c.execute('''
            INSERT INTO alerts (timestamp, camera, label, confidence, status, image)
            VALUES (?, ?, ?, ?, 'unread', ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            camera,
            label,
            int(confidence),
            image
        ))
        conn.commit()
    finally:
        conn.close()

# ────────────────────────────
# Getting Alerts for Frontend
# ────────────────────────────
def get_alerts(limit=100):
    """Fetch alerts as list of dicts"""
    conn = sqlite3.connect(ALERT_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
# ────────────────────────────
# Telegram Bot Notification 
# ────────────────────────────

TG_TOKEN  = os.getenv("TG_TOKEN",  "7794040595:AAGQsqkqn1Cs3_MrLWuUPj67VdNjAS6nT1U") 
TG_CHATID = os.getenv("TG_CHAT",  "1531394637")                                        

def push_telegram(text: str, image_path: str | None = None):
    """Send Telegram text + optional photo."""
    try:
        if image_path and os.path.isfile(image_path):
            url   = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
            files = {"photo": open(image_path, "rb")}
            data  = {"chat_id": TG_CHATID, "caption": text}
        else:
            url   = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            files = None
            data  = {"chat_id": TG_CHATID, "text": text}
        requests.post(url, data=data, files=files, timeout=4)
        print("[TG] pushed")
    except Exception as e:
        print("[TG] push failed:", e)