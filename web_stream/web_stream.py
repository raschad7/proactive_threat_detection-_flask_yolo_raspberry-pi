#!/usr/bin/env python3

"""
Smooth MJPEG stream with YOLOv5 weapon-detection.
  320*320 inference ? faster
  skip N-1 frames out of every N to boost FPS
  sends an alert JSON to backend when weapon > threshold
"""

import cv2
import time
import torch
import datetime
import requests
import importlib.util

from flask import Flask, Response, render_template_string

# ---------------- CONFIG ----------------
MODEL_PATH  =    "/home/asus/best.pt"                # must contain hubconf.py
REPO_DIR    =    "/home/asus/yolov5m"                # must contain hubconf.py
IMG_SIZE    =    320                                 # inference resolution
INFER_EVERY =    3                                   # 1 = every frame, 3 = every 3rd
CONF_THRESH =    40                                  # send alert if conf >= %
CAMERA_NAME =    "Front Door"                        # label in dashboard
API_URL     =    "http://192.168.1.102:5000/api/alert"   # ? EDIT
API_TOKEN   =    ""                                  # optional ^-SEC-TOKEN header
THROTTLE_SEC=    5                                   # avoid duplicate span
MJPEG_BOUND = b'\r\n--frame\r\nContent-Type: image/jpeg\r\n\r\n'

# ====== load YOLOv5 model ======
print("[INFO] loading YOLOv5 model?")
model = torch.hub.load(REPO_DIR, "custom", path=MODEL_PATH, source="local")
print("[INFO] model loaded")

# ========== camera back-end selection ==========
import importlib.util
from typing import Optional, Callable  # ? added

def open_picam() -> Optional[Callable]:
    """Return lambda that grabs a frame from Picamera2, or None if not available."""
    if importlib.util.find_spec("picamera2") is None:
        return None

    try:
        from picamera2 import Picamera2
        pc = Picamera2()
        pc.configure(pc.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"}))
        pc.start()
        print("[INFO] PiCam via picamera2 ?")
        return lambda: pc.capture_array()
    except Exception as e:
        print(f"[WARN] Picamera2 unusable: {e}")
        return None

def open_cvcam(idx: int) -> Optional[Callable]:
    """Return lambda that grabs a frame from a U4L2 device </dev/videoX>."""
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        print(f"[WARN] no camera found @ /dev/video{idx} via OpenCV ?")
        return None
    return lambda: cap.read()[1]

# ====== pick camera backend that works
grab = open_picam() or open_cvcam(4)
if grab is None:
    raise RuntimeError("No camera found. Install picamera2 OR plug a USB cam.")

# ========== ALERT SENDER ==========
last_alert_ts = 0
headers = {"X-SEC-TOKEN": API_TOKEN} if API_TOKEN else {}

def send_alert(label, confidence, frame=None):
    """Send alert + optional screenshot to Flask server."""
    global last_alert_ts

    # throttle duplicates (10 s)
    if time.time() - last_alert_ts < 10:
        return

    filename = None
    # save screenshot to Pi disk first
    if frame is not None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{ts}.jpg"
        dirpath = "/home/asus/website/static/screens"
        os.makedirs(dirpath, exist_ok=True)
        path = os.path.join(dirpath, filename)

        cv2.imwrite(path, frame)
        if os.path.exists(path):
            print("[DEBUG] Screenshot saved:", path)
        else:
            print("[ERROR] Screenshot NOT saved:", path)
            filename = None   # don’t send bad ref

    # build multipart-form payload
    data = {
        "camera": "Pi Camera 1",
        "label": label,
        "confidence": f"{confidence:.1f}",
        "thumb":3
    }
    files = {}
    if filename:
        with open(path, "rb") as f:
            files["screenshot"] = (filename, f.read(), "image/jpeg")

    try:
        r = requests.post(
            "http://192.168.1.102:5000/api/alert",
            data=data,
            files=files,
            headers=headers,
        )
        print(f"[ALERT] {label} {confidence:.1f}% sent – status {r.status_code}")
        last_alert_ts = time.time()
    except Exception as e:
        print("[ALERT] send failed:", e)

# ========= Flask app ===========
app = Flask(__name__)

def mjpeg_generator():
    frame_no = 0
    annotated = None  # last annotated frame

    while True:
        frame = grab()
        if frame is None:
            continue

        # Inference every INFER_EVERY frames
        if frame_no % INFER_EVERY == 0:
            small = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
            results = model(small, size=IMG_SIZE)

            # ====== alert logic ======
            for xxyy, conf, cls in results.xyxy[0]:
                label = model.names[int(cls)]
                conf_val = float(conf) * 100
                print(f"[DETECT] label={label}, confidence={conf_val:.1f}%")  # debug

                if conf_val >= CONF_THRESH:    # ? no label filter for now
                    send_alert(label, conf_val, annotated)  # send only one alert per frame
                    break

            # render annotated frame (outside the for-loop)
            annotated_small = results.render()[0]
            annotated = cv2.resize(
                annotated_small,
                (frame.shape[1], frame.shape[0])
            )

        frame_no += 1

        view = annotated if annotated is not None else frame
        ok, buf = cv2.imencode(".jpg", view, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue
        yield MJPEG_BOUND + buf.tobytes() + b"\r\n"

@app.route("/")
def index():
    return render_template_string(
        "<h2>Weapon-Detection Stream</h2>"
        '<img src="/video" width="800" />'
    )

@app.route("/video")
def video():
    return Response(
        mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

# ========== run ==========
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

