# main.py
# ─────────────────────────────────────────
#  Driver Drowsy Detection System
#  Phase 2 - Multi Signal Detection
#
#  ALERT LOGIC:
#  Any signal  -> Audio alarm loops immediately
#  After 6 sec -> Call + SMS + WhatsApp + Email
#  Driver wakes -> Audio stops automatically
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

CAMERA_INDEX = 0
WINDOW_NAME  = "DDS - Driver Drowsy Detection  |  Press Q to quit"


def main():
    print("=" * 55)
    print("   Driver Drowsy Detection System (DDS)")
    print("   Phase 2 - Multi-Signal Detection")
    print("=" * 55)
    print("   AUDIO  : Starts immediately on any signal")
    print("   CALLS  : Fire after 6 seconds of drowsiness")
    print("   AUDIO  : Stops when driver wakes up")
    print("=" * 55)
    print(f"   Started : {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 55)
    print("   Press Q to quit\n")

    try:
        eye_detector  = DrowsinessDetector()
        yawn_detector = YawnDetector()
        head_detector = HeadPoseDetector()
        perclos       = PERCLOSTracker()
        alerter       = AlertManager()
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh    = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {CAMERA_INDEX}.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    print("[INFO] Webcam opened. Monitoring started...\n")

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

            rgb       = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_result = face_mesh.process(rgb)

            # ── Collect signals ───────────
            alert_score   = 0
            alert_reasons = []

            # Eye EAR
            eye_result = eye_detector.process_frame(frame)
            frame      = eye_result["frame"]
            ear        = eye_result["ear"]

            if eye_result["alert"]:
                alert_score += 1
                alert_reasons.append("Eyes Closed")

            # PERCLOS
            if ear > 0:
                perclos.update(ear)
                frame = perclos.draw(frame)
                if perclos.level == "HIGH":
                    alert_score += 1
                    alert_reasons.append("PERCLOS High")

            # Yawn + Head Pose
            if mp_result.multi_face_landmarks:
                landmarks = mp_result.multi_face_landmarks[0].landmark

                yawn_result = yawn_detector.process(landmarks, frame, w, h)
                frame       = yawn_result["frame"]
                if yawn_result["yawning"]:
                    alert_score += 1
                    alert_reasons.append("Yawning")

                pose_result = head_detector.process(landmarks, frame, w, h)
                frame       = pose_result["frame"]
                if pose_result["nodding"]:
                    alert_score += 1
                    alert_reasons.append("Head Nod")
                if pose_result["tilting"]:
                    alert_score += 1
                    alert_reasons.append("Head Tilt")

            # ── Update alert manager ──────
            is_drowsy = alert_score >= 1
            reason    = ", ".join(alert_reasons)
            alerter.update(is_drowsy=is_drowsy, alert_score=alert_score, reason=reason)

            # ── Countdown overlay ─────────
            if is_drowsy:
                countdown = alerter.get_countdown()
                confirmed = alerter.is_confirmed()

                if confirmed:
                    # Red pulsing border
                    cv2.rectangle(frame, (0, 0), (639, 479), (0, 0, 255), 4)
                    cv2.rectangle(frame, (0, 0), (640, 48), (0, 0, 180), -1)
                    cv2.putText(frame, "DROWSINESS CONFIRMED - CALLING NOW",
                                (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:
                    # Orange border
                    cv2.rectangle(frame, (0, 0), (639, 479), (0, 140, 255), 3)
                    # Countdown bar
                    progress = 1.0 - (countdown / alerter.CONFIRM_SECONDS)
                    bar_w    = int(620 * progress)
                    cv2.rectangle(frame, (10, 460), (630, 475), (50, 50, 50), -1)
                    cv2.rectangle(frame, (10, 460), (10 + bar_w, 475), (0, 140, 255), -1)
                    cv2.putText(frame, f"Calling in {countdown:.1f}s...",
                                (10, 453), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 1)

            # ── Status ────────────────────
            if not is_drowsy:
                if eye_result["face_detected"]:
                    cv2.putText(frame, "Monitoring...", (10, 455),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 0), 1)
                else:
                    cv2.putText(frame, "No Face Detected", (10, 455),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 1)

            # Score badge
            score_color = (0, 0, 255) if alert_score >= 2 else \
                          (0, 140, 255) if alert_score == 1 else (0, 200, 0)
            cv2.putText(frame, f"Signals: {alert_score}", (490, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, score_color, 2)

            # FPS
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps         = frame_count
                frame_count = 0
                fps_time    = time.time()
            cv2.putText(frame, f"FPS:{fps}", (580, 455),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)

            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n[INFO] Shutting down.")
                break

        except Exception as e:
            print(f"[ERROR] {e}")
            traceback.print_exc()
            break

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()
    alerter._audio.stop()

    print(f"\n{'='*45}")
    print(f"  Session Summary")
    print(f"{'='*45}")
    print(f"  Critical alerts : {alerter._alert_count}")
    print(f"  Yawns detected  : {yawn_detector.yawn_count}")
    print(f"  Final PERCLOS   : {perclos.perclos:.0%}")
    print(f"{'='*45}\n")


if __name__ == "__main__":
    main()