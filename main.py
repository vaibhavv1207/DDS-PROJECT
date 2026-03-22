# main.py
# ─────────────────────────────────────────
#  Driver Drowsy Detection System
#  Phase 2 – Multi-Signal Detection
#
#  ALERT LOGIC:
#  🔊 Audio  → fires immediately on ANY signal
#  📱 Call/SMS/WhatsApp/Email → fires only when
#     driver is confirmed SLEEPY (score >= 2)
# ─────────────────────────────────────────

import cv2
import time
import traceback
import numpy as np
import mediapipe as mp
from datetime import datetime

from phase1_core.detector           import DrowsinessDetector
from phase1_core.alerter            import AlertManager
from phase2_detection.yawn_detector import YawnDetector
from phase2_detection.head_pose     import HeadPoseDetector
from phase2_detection.perclos       import PERCLOSTracker

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
CAMERA_INDEX = 0
WINDOW_NAME  = "DDS – Phase 2  |  Press Q to quit"

# Alert channels split by severity
EARLY_ALERT_CHANNELS    = ["audio"]                              # any 1 signal
CRITICAL_ALERT_CHANNELS = ["audio", "sms", "call",
                            "whatsapp", "email"]                 # confirmed sleepy

# How many signals needed to trigger CRITICAL alerts
# 1 = just eyes closing is enough
# 2 = need 2 signals (e.g. eyes + yawn, or eyes + nod) ← recommended
# 3 = very strict (3 signals together)
CRITICAL_SCORE_THRESHOLD = 2


def main():
    print("=" * 55)
    print("   Driver Drowsy Detection System (DDS)")
    print("   Phase 2 – Multi-Signal Detection")
    print("=" * 55)
    print(f"   Early alert  : Audio only (any 1 signal)")
    print(f"   Critical     : Call+SMS+WhatsApp+Email")
    print(f"   Confirmed at : {CRITICAL_SCORE_THRESHOLD} signals simultaneously")
    print(f"   Started      : {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 55)
    print("   Press Q to quit\n")

    # ── Load detectors ────────────────────
    try:
        eye_detector  = DrowsinessDetector()
        yawn_detector = YawnDetector()
        head_detector = HeadPoseDetector()
        perclos       = PERCLOSTracker()
    except Exception as e:
        print(f"[ERROR] Failed to load detectors: {e}")
        traceback.print_exc()
        return

    # Two alerters — different cooldowns
    early_alerter    = AlertManager(cooldown=10)   # audio every 10s
    critical_alerter = AlertManager(cooldown=30)   # calls every 30s

    # ── MediaPipe shared face mesh ────────
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh    = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    # ── Open webcam ───────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {CAMERA_INDEX}.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print("[INFO] Webcam opened. Starting detection...\n")

    fps_time    = time.time()
    frame_count = 0
    fps         = 0

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[ERROR] Failed to grab frame.")
                break

            frame = cv2.resize(frame, (640, 480))
            h, w  = frame.shape[:2]

            # ── Shared MediaPipe pass ─────
            rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_result = face_mesh.process(rgb)

            # ── Signal collection ─────────
            alert_score   = 0
            alert_reasons = []

            # ── Phase 1: Eye EAR ──────────
            eye_result = eye_detector.process_frame(frame)
            frame      = eye_result["frame"]
            ear        = eye_result["ear"]

            if eye_result["alert"]:
                alert_score += 1
                alert_reasons.append("EYES CLOSED")

            # ── PERCLOS ───────────────────
            if ear > 0:
                perclos.update(ear)
                frame = perclos.draw(frame)
                if perclos.level == "HIGH":
                    alert_score += 1
                    alert_reasons.append("PERCLOS HIGH")

            # ── Phase 2: Yawn + Head Pose ─
            if mp_result.multi_face_landmarks:
                landmarks = mp_result.multi_face_landmarks[0].landmark

                yawn_result = yawn_detector.process(landmarks, frame, w, h)
                frame       = yawn_result["frame"]
                if yawn_result["yawning"]:
                    alert_score += 1
                    alert_reasons.append("YAWNING")

                pose_result = head_detector.process(landmarks, frame, w, h)
                frame       = pose_result["frame"]
                if pose_result["nodding"]:
                    alert_score += 1
                    alert_reasons.append("HEAD NOD")
                if pose_result["tilting"]:
                    alert_score += 1
                    alert_reasons.append("HEAD TILT")

            # ════════════════════════════════
            #  ALERT DECISION LOGIC
            # ════════════════════════════════

            if alert_score >= 1:
                # ── Early alert: audio only ──
                early_alerter.trigger(channels=["audio"])

            if alert_score >= CRITICAL_SCORE_THRESHOLD:
                # ── Critical: confirmed sleepy ──
                # Only fire call/sms/etc when truly drowsy
                critical_alerter.trigger(
                    channels=CRITICAL_ALERT_CHANNELS,
                    reason=", ".join(alert_reasons)
                )

            # ── Status display ────────────
            if alert_score >= CRITICAL_SCORE_THRESHOLD:
                status_text  = f"SLEEPY! [{', '.join(alert_reasons)}]"
                status_color = (0, 0, 255)
                # Red border around frame
                cv2.rectangle(frame, (0, 0), (639, 479), (0, 0, 255), 3)

            elif alert_score == 1:
                status_text  = f"WARNING: {alert_reasons[0]}"
                status_color = (0, 165, 255)
                # Orange border
                cv2.rectangle(frame, (0, 0), (639, 479), (0, 165, 255), 2)

            elif eye_result["face_detected"]:
                status_text  = "Monitoring..."
                status_color = (0, 255, 0)
            else:
                status_text  = "No Face Detected"
                status_color = (0, 165, 255)

            # Bottom status bar
            cv2.rectangle(frame, (0, 455), (640, 480), (20, 20, 20), -1)
            cv2.putText(frame, status_text, (10, 472),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)

            # Score indicator top right
            score_color = (0, 0, 255) if alert_score >= CRITICAL_SCORE_THRESHOLD else \
                          (0, 165, 255) if alert_score >= 1 else (0, 200, 0)
            cv2.putText(frame, f"Score:{alert_score}", (540, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, score_color, 2)

            # FPS + alert counts
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps         = frame_count
                frame_count = 0
                fps_time    = time.time()
            cv2.putText(frame, f"FPS:{fps}", (540, 472),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

            cv2.imshow(WINDOW_NAME, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n[INFO] Q pressed – shutting down.")
                break

        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()
            break

    # ── Cleanup ───────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    print(f"\n{'='*45}")
    print(f"  Session Summary")
    print(f"{'='*45}")
    print(f"  Total critical alerts : {critical_alerter._alert_count}")
    print(f"  Total early warnings  : {early_alerter._alert_count}")
    print(f"  Total yawns detected  : {yawn_detector.yawn_count}")
    print(f"  Final PERCLOS score   : {perclos.perclos:.0%}")
    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()