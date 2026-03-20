# main.py
import cv2
import time
import traceback
from datetime import datetime
from phase1_core.detector import DrowsinessDetector
from phase1_core.alerter  import AlertManager

CAMERA_INDEX   = 0
WINDOW_NAME    = "DDS – Driver Drowsy Detection  |  Press Q to quit"
ALERT_CHANNELS = ["audio", "sms", "call", "whatsapp", "email"]

def main():
    print("=" * 50)
    print("   Driver Drowsy Detection System (DDS)")
    print("   Phase 1 – Core Detection + Alerting")
    print("=" * 50)
    print(f"   Camera    : {CAMERA_INDEX}")
    print(f"   Alerts    : {', '.join(ALERT_CHANNELS)}")
    print(f"   Started   : {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    print("   Press Q to quit\n")

    try:
        detector = DrowsinessDetector()
    except Exception as e:
        print(f"[ERROR] Detector failed to load: {e}")
        traceback.print_exc()
        return

    alerter = AlertManager()

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

            result = detector.process_frame(frame)

            if result["alert"]:
                alerter.trigger(channels=ALERT_CHANNELS)

            # FPS
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps         = frame_count
                frame_count = 0
                fps_time    = time.time()

            # Status
            status_text  = "DROWSY!" if result["alert"] else ("Awake" if result["face_detected"] else "No Face")
            status_color = (0, 0, 255) if result["alert"] else ((0, 255, 0) if result["face_detected"] else (0, 165, 255))
            cv2.putText(result["frame"], f"Status: {status_text}", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(result["frame"], f"FPS: {fps}",
                        (10, result["frame"].shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
            cv2.putText(result["frame"], f"Alerts: {alerter._alert_count}",
                        (result["frame"].shape[1] - 120, result["frame"].shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

            cv2.imshow(WINDOW_NAME, result["frame"])

            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("\n[INFO] Q pressed – shutting down.")
                break

        except Exception as e:
            print(f"[ERROR] Frame processing error: {e}")
            traceback.print_exc()
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n[INFO] Session ended. Total alerts: {alerter._alert_count}")

if __name__ == "__main__":
    main()