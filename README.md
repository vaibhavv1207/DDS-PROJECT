# 🚗 Driver Drowsy Detection System (DDS)

> A real-time, software-only drowsiness detection system using computer vision — built phase by phase.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-green?style=flat-square&logo=opencv)
![Twilio](https://img.shields.io/badge/Twilio-Alerts-red?style=flat-square&logo=twilio)
![Status](https://img.shields.io/badge/Status-Phase%201%20Active-orange?style=flat-square)

---

## 📌 What is DDS?

DDS monitors a driver's face in real time using a webcam. When drowsiness is detected (eyes closing too long), it immediately fires alerts via sound, SMS, WhatsApp, and a phone call — all from software, no hardware modifications needed.

---

## 🗺️ Project Roadmap

```
Phase 1 – Core Foundation          ← YOU ARE HERE
Phase 2 – Detection Enhancements
Phase 3 – Fatigue Intelligence
Phase 4 – Dashboard & Logging
Phase 5 – Performance & Deployment
```

---

## ✅ Phase 1 – Core Foundation *(Current)*

**Goal:** Get the basic system running with alerting.

| Feature | Status | File |
|---|---|---|
| Face + Eye Detection (EAR) | ✅ Done | `phase1_core/detector.py` |
| Twilio Voice Call Alert | ✅ Done | `phase1_core/alerter.py` |
| Twilio SMS Alert | ✅ Done | `phase1_core/alerter.py` |
| WhatsApp Alert | ✅ Done | `phase1_core/alerter.py` |
| Email Alert (Gmail) | ✅ Done | `phase1_core/alerter.py` |
| Audio Alarm | ✅ Done | `phase1_core/alerter.py` |

---

## 🔜 Phase 2 – Detection Enhancements

**Goal:** Add more drowsiness signals beyond just eyes.

| Feature | Status | Details |
|---|---|---|
| Yawn Detection (MAR) | 🔲 Planned | Mouth Aspect Ratio via dlib |
| Head Pose Estimation | 🔲 Planned | Nodding/tilting via solvePnP |
| PERCLOS Metric | 🔲 Planned | Rolling eye-closure score |
| Phone Use Detection | 🔲 Planned | YOLOv8 / MediaPipe Hands |
| Gaze Direction | 🔲 Planned | Iris landmark tracking |

---

## 🔜 Phase 3 – Fatigue Intelligence

**Goal:** Combine all signals into a smart fatigue score.

| Feature | Status | Details |
|---|---|---|
| Fatigue Score Engine | 🔲 Planned | Weighted EAR+MAR+Pose score |
| CNN Classifier | 🔲 Planned | MobileNetV2 on eye patches |
| Session Trend Analysis | 🔲 Planned | Predict high-risk windows |

---

## 🔜 Phase 4 – Dashboard & Logging

**Goal:** Visualize and store everything.

| Feature | Status | Details |
|---|---|---|
| Web Dashboard | 🔲 Planned | Flask + Chart.js live feed |
| Incident Video Clip | 🔲 Planned | 10s clip on HIGH alert |
| PDF Trip Report | 🔲 Planned | ReportLab auto-generate |
| SQLite Event Log | 🔲 Planned | Full alert history DB |

---

## 🔜 Phase 5 – Performance & Deployment

**Goal:** Make it fast, portable, and deployable.

| Feature | Status | Details |
|---|---|---|
| Threading Optimization | 🔲 Planned | 30 FPS stable |
| Docker Container | 🔲 Planned | Cross-platform deploy |
| Low-Light Enhancement | 🔲 Planned | CLAHE preprocessing |
| TFLite / ONNX Export | 🔲 Planned | Fast CPU inference |

---

## 📁 Project Structure

```
dds/
├── main.py                        # Entry point – run this
├── requirements.txt               # All dependencies
├── .env.example                   # Config template (copy to .env)
├── .gitignore
│
├── phase1_core/
│   ├── detector.py                # Face + eye detection (EAR)
│   └── alerter.py                 # All alert channels
│
├── phase2_detection/              # Yawn, head pose, PERCLOS (Phase 2)
├── phase3_fatigue/                # Fatigue score engine (Phase 3)
├── phase4_dashboard/              # Flask dashboard (Phase 4)
├── phase5_deployment/             # Docker, optimization (Phase 5)
│
├── models/                        # dlib model file goes here
├── assets/sounds/                 # alarm.mp3 goes here
├── logs/                          # SQLite DB, log files
├── clips/                         # Incident video clips
└── reports/                       # PDF trip reports
```

---

## 🚀 Setup & Run (Phase 1)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/dds.git
cd dds
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download dlib model
Download `shape_predictor_68_face_landmarks.dat` from:
http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

Extract and place in the `models/` folder.

### 5. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your Twilio credentials and phone numbers
```

### 6. Run
```bash
python main.py
```

Press **Q** to quit.

---

## ⚙️ Configuration

Edit `.env` to tune detection:

| Variable | Default | Description |
|---|---|---|
| `EAR_THRESHOLD` | `0.25` | Lower = more sensitive |
| `EAR_CONSEC_FRAMES` | `20` | Frames before alert fires |
| `TWILIO_ACCOUNT_SID` | – | From Twilio Console |
| `ALERT_PHONE_NUMBER` | – | Emergency contact number |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Detection | OpenCV, dlib 68-point landmarks |
| Alerting | Twilio (Call/SMS/WhatsApp), smtplib |
| Audio | playsound |
| Dashboard *(Phase 4)* | Flask, Chart.js, SocketIO |
| ML *(Phase 3)* | TensorFlow / MobileNetV2 |

---

## 📄 License

MIT License © 2025