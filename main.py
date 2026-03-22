# main.py
# ─────────────────────────────────────────
#  Driver Drowsy Detection System
#  Phase 2 – Multi-Signal Detection
#  Run: python main.py
# ─────────────────────────────────────────

import cv2
import time
import traceback
from datetime import datetime

# Phase 1
from phase1_core.detector import DrowsinessDetector
from phase1_core.alerter  import AlertManager

# Phase 2
from phase2_detection.yawn_detector import YawnDetector
from phase2_detection.head_pose     import HeadPoseDetector
from phase2_detection.perclos       import PERCLOSTracker

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
CAMERA_INDEX   = 0
WINDOW_NAME    = "DDS – Phase 2  |  Press Q to quit"
ALERT_CHANNELS = ["audio", "sms", "call", "whatsapp", "email"]

# Alert scoring — how many signals needed to fire alert
# 1 = any single signal triggers alert
# 2 = two signals needed (less false positives)
ALERT_SCORE_THRESHOLD = 1


def main():
    print("=" * 55)
    print("   Driver Drowsy Detection System (DDS)")
    print("   Phase 2 – Multi-Signal Detection")
    print("=" * 55)
    print(f"   Signals  : EAR + Yawn + Head Pose + PERCLOS")
    print(f"   Alerts   : {', '.join(ALERT_CHANNELS)}")
    print(f"   Started  : {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 55)
    print("   Press Q to quit\n")

    # ── Load all detectors ────────────────
    try:
        eye_detector  = DrowsinessDetector()
        yawn_detector = YawnDetector()
        head_detector = HeadPoseDetector()
        perclos       = PERCLOSTracker()
        alerter       = AlertManager()
    except Exception as e:
        print(f"[ERROR] Failed to load detectors: {e}")
        traceback.print_exc()
        return

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

    # ── Import mediapipe for shared face mesh ──
    import mediapipe as mp
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh    = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[ERROR] Failed to grab frame.")
                break

            frame = cv2.resize(frame, (640, 480))
            h, w  = frame.shape[:2]

            # ── Shared MediaPipe processing ───
            import numpy as np
            rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_result = face_mesh.process(rgb)

            # ── Signal scores ─────────────────
            alert_score   = 0
            alert_reasons = []

            # Phase 1 – Eye detection (EAR)
            eye_result = eye_detector.process_frame(frame)
            frame      = eye_result["frame"]
            ear        = eye_result["ear"]

            if eye_result["alert"]:
                alert_score += 1
                alert_reasons.append("EYES")

            # Update PERCLOS
            if ear > 0:
                perclos.update(ear)
                frame = perclos.draw(frame)
                if perclos.level == "HIGH":
                    alert_score += 1
                    alert_reasons.append("PERCLOS")

            # Phase 2 – Yawn + Head Pose
            if mp_result.multi_face_landmarks:
                landmarks = mp_result.multi_face_landmarks[0].landmark

                # Yawn detection
                yawn_result = yawn_detector.process(landmarks, frame, w, h)
                frame        = yawn_result["frame"]
                if yawn_result["yawning"]:
                    alert_score += 1
                    alert_reasons.append("YAWN")

                # Head pose
                pose_result = head_detector.process(landmarks, frame, w, h)
                frame        = pose_result["frame"]
                if pose_result["nodding"]:
                    alert_score += 1
                    alert_reasons.append("NOD")
                if pose_result["tilting"]:
                    alert_score += 1
                    alert_reasons.append("TILT")

            # ── Fire alert if score reached ───
            if alert_score >= ALERT_SCORE_THRESHOLD:
                alerter.trigger(channels=ALERT_CHANNELS)

            # ── Status bar ────────────────────
            if alert_score >= ALERT_SCORE_THRESHOLD and alert_reasons:
                status_text  = f"ALERT: {', '.join(alert_reasons)}"
                status_color = (0, 0, 255)
            elif eye_result["face_detected"]:
                status_text  = "Monitoring..."
                status_color = (0, 255, 0)
            else:
                status_text  = "No Face Detected"
                status_color = (0, 165, 255)

            # Status bottom bar
            cv2.rectangle(frame, (0, 455), (640, 480), (30, 30, 30), -1)
            cv2.putText(frame, status_text, (10, 472),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 1)

            # FPS top right
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps         = frame_count
                frame_count = 0
                fps_time    = time.time()

            cv2.putText(frame, f"FPS:{fps} | Alerts:{alerter._alert_count}",
                        (440, 472), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

            # ── Show frame ────────────────────
            cv2.imshow(WINDOW_NAME, frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n[INFO] Q pressed – shutting down.")
                break

        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()
            break

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    print(f"\n[INFO] Session ended.")
    print(f"[INFO] Total alerts : {alerter._alert_count}")
    print(f"[INFO] Total yawns  : {yawn_detector.yawn_count}")
    print(f"[INFO] Final PERCLOS: {perclos.perclos:.0%}")


if __name__ == "__main__":
    main()