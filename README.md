```markdown
# 🔐 Proactive Threat Detection System (Raspberry Pi + Flask + YOLOv5)

A real-time edge-based surveillance system that detects **handguns and knives**, saves annotated screenshots, logs alerts, and sends instant push notifications via **Telegram** — all powered by **YOLOv5**, a **Flask web dashboard**, and a **Raspberry Pi 4**.

---

## 📸 System Overview

- 🧠 **Raspberry Pi 4 (8GB)** runs an optimized YOLOv5s model for real-time weapon detection.
- 💻 **Flask Web App** displays alerts, screenshots, camera feed, logs, and system metrics.
- 🔔 **Telegram Bot** sends alerts with annotated images instantly.
- 📷 **USB Camera** captures live video stream.
- 💾 **Local SQLite DBs** store alert history and system logs.

---

## ⚙️ Hardware Setup

| Component            | Purpose                     |
| -------------------- | --------------------------- |
| Raspberry Pi 4 (8GB) | Main compute & AI inference |
| USB Camera           | Real-time video input       |
| Flash Drive (USB)    | Storage for images & DBs    |
| Power Supply         | Stable 5V/3A recommended    |
| Wi-Fi Connection     | Local network communication |

---

## 🚀 Features

- ✅ Detects **handguns and knives** using a custom YOLOv5s model
- 🖼️ Saves **annotated screenshots** of threats above confidence threshold
- 📡 Pushes alerts to Telegram in real-time
- 🧠 Runs fully on **CPU**, optimized for Raspberry Pi
- 🌐 Flask dashboard: camera feed, alert drawer, filter chips, Pi stats, logs
- 📁 SQLite databases: `alerts.db` and `logs.db`
- 📲 Responsive design: works on desktop & mobile

---

## 🧱 Project Structure
```

SecuritySystem/
├── website/ # Flask app
│ ├── templates/ # HTML pages
│ ├── static/ # JS/CSS + screenshots
│ │ └── screens/ # saved alert images
│ ├── views.py # API and route logic
│ ├── utils.py # DB and Telegram helpers
│ └── **init**.py # Flask app init
├── web_stream.py # Raspberry Pi main script
├── alerts.db / logs.db # SQLite databases
├── best.pt # Trained YOLOv5s model (gun + knife)
├── requirements.txt
└── README.md

````

---

## 🧪 AI Model Details

- YOLOv5s fine-tuned on ~2200 handgun + knife images
- Dataset cleaned & relabeled (pistol: 0, knife: 1)
- Training: 80 epochs, mAP@50 ≈ 0.97
- Exported as TorchScript & ONNX (FP16)
- Screenshot saved when confidence ≥ 70%

---

## 📥 Installation (Web Server / Dashboard)

> Requires: Python 3.8+, pip, virtualenv

```bash
git clone https://github.com/your-user/threat-detection-pi.git
cd threat-detection-pi
python -m venv venv && source venv/bin/activate     # On Windows: venv\Scripts\activate
pip install -r requirements.txt
````

### Set environment variables (or use `.env`)

```bash
export TG_TOKEN="your-telegram-bot-token"
export TG_CHAT="your-chat-id"
```

### Start Flask server

```bash
cd website
python app.py
```

---

## 🤖 Raspberry Pi Setup

### 1. Connect camera

Plug a USB camera into the Pi.

### 2. Install dependencies

```bash
sudo apt update && sudo apt install python3-pip
pip install torch torchvision opencv-python requests
```

### 3. Transfer files

```bash
scp web_stream.py pi@<pi-ip>:/home/pi/
scp best.pt       pi@<pi-ip>:/home/pi/
```

### 4. Run detection

```bash
python3 web_stream.py
```

This will:

- Start the camera feed
- Run YOLOv5 detection
- Send a POST with label/confidence + screenshot to `/api/alert`

---

## 📡 Alert API

```http
POST /api/alert
Headers: X-SEC-TOKEN: your-secret
Body: form-data (label, confidence, camera, screenshot)
```

---

## 💬 Telegram Integration

- Create bot via [@BotFather](https://t.me/BotFather)
- Get your `TG_TOKEN` and `chat_id`
- Alerts with screenshots will be pushed instantly

---

## 🧰 Environment Variables

| Variable    | Description                          |
| ----------- | ------------------------------------ |
| `TG_TOKEN`  | Your Telegram bot token              |
| `TG_CHAT`   | Your Telegram chat ID                |
| `API_TOKEN` | Secret key for POST request security |

---

## 🧾 Sample Alert Flow

1. Pi detects a handgun (76%)
2. Captures a frame, saves screenshot
3. Sends POST to Flask `/api/alert`
4. Flask saves alert to DB, image to `static/screens`
5. Alert appears in UI + Telegram notification sent

---

## 🐛 Known Issues

- Low FPS (\~5–7) on Pi 4 with YOLOv5s (CPU)
- Telegram API blocked on slow/unstable connections
- Use SD card or SSD for faster disk IO

---

## 🛡️ Security Note

- Never hard-code bot tokens or passwords
- Use `.env` + `os.getenv()` and ensure `.env` is in `.gitignore`

---

## 📜 License

MIT License – free to use, modify, and distribute.

---

## 🙌 Credits

- YOLOv5 by Ultralytics
- OpenCV for image processing
- Flask for the dashboard
- Telegram Bot API

```

You can save this content as `README.md` in your repo root and modify the repo link, author, or model details as needed.
Let me know if you want to add demo images, architecture diagrams, or video walkthroughs.
```
