````markdown
# 🔍 Raspberry-Pi Weapon-Alert System

Real-time gun & knife detection that runs on a Raspberry Pi and shows alerts on a simple Flask web dashboard.

---

## What It Does
1. **Pi grabs camera video** (USB / PiCam, ~10 FPS).
2. **YOLOv5-s model** spots hand-guns & knives (≥ 70 % confidence).
3. Saves an **annotated screenshot**.
4. Sends the alert + image to a **Flask server** on your laptop/PC.
5. Dashboard pops the alert and sends a **Telegram push**.

---

## Hardware Needed
| Item              | Notes               |
|-------------------|---------------------|
| Raspberry Pi 4/5  | 4 GB or 8 GB works  |
| USB / Pi Camera   | 640 × 480 is fine   |
| 5 V 3 A PSU       | Stable power        |
| (Optional) Fan    | Keeps FPS steady    |

---

## Quick Start

### 1. Clone & install (PC side)
```bash
git clone https://github.com/your-user/pi-weapon-alert.git
cd pi-weapon-alert
python -m venv venv && source venv/bin/activate   # Win: venv\Scripts\activate
pip install -r requirements.txt
export TG_TOKEN="YOUR_BOT_TOKEN"
export TG_CHAT="YOUR_CHAT_ID"
python website/app.py --host 0.0.0.0 --port 5000
````

### 2. Set up Pi

```bash
scp web_stream.py best.pt pi@<pi-ip>:/home/pi/
ssh pi@<pi-ip>
pip install torch torchvision opencv-python requests
python web_stream.py       # starts detection & sends alerts
```

Open browser → `http://<pc-ip>:5000` to see the dashboard.

---

## Folder Overview

```
website/          # Flask app (HTML, CSS, JS, routes)
web_stream.py     # Pi script: camera + YOLO + alert POST
best.pt           # Trained YOLOv5-s weights (guns & knives)
requirements.txt  # pip packages
```

---

## Key Features

* **Real-time detection** on low-cost hardware
* **Screenshot evidence** stored automatically
* **Telegram push** with image (free)
* **Dark-mode dashboard**: live video, alerts, Pi metrics
* All local — no cloud fees

---

## To-Do / Ideas

* Quantise model (INT8) for higher FPS
* Add email fallback
* Auto-prune old screenshots

---

## License

MIT

```
```
