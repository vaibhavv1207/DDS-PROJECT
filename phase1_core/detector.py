# phase1_core/detector.py
# ─────────────────────────────────────────
#  Core Face + Eye Detection Engine
#  Uses dlib 68-point facial landmarks
#  Calculates Eye Aspect Ratio (EAR)
# ─────────────────────────────────────────

import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
from imutils import face_utils
import os
from dotenv import load_dotenv

load_dotenv()

# ── Load thresholds from .env ────────────
EAR_THRESHOLD     = float(os.getenv("EAR_THRESHOLD", 0.25))
EAR_CONSEC_FRAMES = int(os.getenv("EAR_CONSEC_FRAMES", 20))
MODEL_PATH        = os.getenv("DLIB_MODEL_PATH", "models/shape_predictor_68_face_landmarks.dat")

# ── dlib landmark indices for eyes ───────
(L_START, L_END) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(R_START, R_END) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)


class DrowsinessDetector:

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"\n[ERROR] dlib model not found at: '{MODEL_PATH}'\n"
                "Download: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2\n"
                "Extract the .dat file and place it inside the models/ folder.\n"
            )
        print("[INFO] Loading dlib face detector...")
        self.detector  = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(MODEL_PATH)
        print("[INFO] Detector loaded successfully.")
        self.frame_counter   = 0
        self.alert_triggered = False
        self.total_alerts    = 0

    def process_frame(self, frame):

        # Resize to 640x480 for consistent processing
        frame = cv2.resize(frame, (640, 480))

        # Convert BGR→RGB for dlib (dlib requires RGB not BGR)
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Force contiguous uint8 arrays
        rgb  = np.ascontiguousarray(rgb,  dtype=np.uint8)
        gray = np.ascontiguousarray(gray, dtype=np.uint8)

        # Detect faces using RGB image
        rects = self.detector(rgb, 0)

        result = {
            "ear"          : 0.0,
            "alert"        : False,
            "face_detected": False,
            "frame_counter": self.frame_counter,
            "frame"        : frame.copy(),
        }

        for rect in rects:
            result["face_detected"] = True

            # Get 68 facial landmarks (use gray for predictor)
            shape     = self.predictor(gray, rect)
            shape     = face_utils.shape_to_np(shape)

            left_eye  = shape[L_START:L_END]
            right_eye = shape[R_START:R_END]

            left_ear  = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear       = (left_ear + right_ear) / 2.0
            result["ear"] = round(ear, 3)

            # Draw eye contours
            for eye in [left_eye, right_eye]:
                hull = cv2.convexHull(eye)
                cv2.drawContours(result["frame"], [hull], -1, (0, 255, 0), 1)

            # Draw face bounding box
            x, y, w, h = rect.left(), rect.top(), rect.width(), rect.height()
            cv2.rectangle(result["frame"], (x, y), (x + w, y + h), (255, 255, 0), 1)

            # EAR threshold check
            if ear < EAR_THRESHOLD:
                self.frame_counter += 1

                # Drowsiness meter bar
                progress = min(self.frame_counter / EAR_CONSEC_FRAMES, 1.0)
                bar_w    = int(300 * progress)
                cv2.rectangle(result["frame"], (10, 130), (310, 150), (50, 50, 50), -1)
                color = (0, 165, 255) if progress < 0.7 else (0, 0, 255)
                cv2.rectangle(result["frame"], (10, 130), (10 + bar_w, 150), color, -1)
                cv2.putText(result["frame"], "Drowsiness meter:", (10, 125),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                if self.frame_counter >= EAR_CONSEC_FRAMES:
                    result["alert"] = True
                    self.alert_triggered = True
                    self.total_alerts   += 1
                    cv2.rectangle(result["frame"], (0, 0), (640, 45), (0, 0, 180), -1)
                    cv2.putText(result["frame"], "!! DROWSINESS ALERT !!", (30, 32),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            else:
                self.frame_counter   = 0
                self.alert_triggered = False

            # HUD
            cv2.putText(result["frame"], f"EAR: {ear:.3f}", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
            cv2.putText(result["frame"], f"Threshold: {EAR_THRESHOLD}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            cv2.putText(result["frame"], f"Frames: {self.frame_counter}/{EAR_CONSEC_FRAMES}",
                        (10, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

            result["frame_counter"] = self.frame_counter
            break

        if not result["face_detected"]:
            cv2.putText(result["frame"], "No face detected", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)

        return result

    def reset(self):
        self.frame_counter   = 0
        self.alert_triggered = False