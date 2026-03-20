# phase1_core/detector.py
import cv2
import numpy as np
import mediapipe as mp
from scipy.spatial import distance as dist
import os
from dotenv import load_dotenv

load_dotenv()

EAR_THRESHOLD     = float(os.getenv("EAR_THRESHOLD", 0.25))
EAR_CONSEC_FRAMES = int(os.getenv("EAR_CONSEC_FRAMES", 20))

LEFT_EYE  = [33,  160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(landmarks, eye_indices, w, h):
    pts = []
    for idx in eye_indices:
        lm = landmarks[idx]
        pts.append((lm.x * w, lm.y * h))
    A = dist.euclidean(pts[1], pts[5])
    B = dist.euclidean(pts[2], pts[4])
    C = dist.euclidean(pts[0], pts[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)

class DrowsinessDetector:

    def __init__(self):
        print("[INFO] Loading MediaPipe Face Mesh...")
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh    = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        print("[INFO] MediaPipe loaded successfully.")
        self.frame_counter   = 0
        self.alert_triggered = False
        self.total_alerts    = 0

    def process_frame(self, frame):
        frame  = cv2.resize(frame, (640, 480))
        h, w   = frame.shape[:2]
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result_mp = self.face_mesh.process(rgb)

        result = {
            "ear"          : 0.0,
            "alert"        : False,
            "face_detected": False,
            "frame_counter": self.frame_counter,
            "frame"        : frame.copy(),
        }

        if result_mp.multi_face_landmarks:
            result["face_detected"] = True
            landmarks = result_mp.multi_face_landmarks[0].landmark

            left_ear  = eye_aspect_ratio(landmarks, LEFT_EYE,  w, h)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
            ear       = (left_ear + right_ear) / 2.0
            result["ear"] = round(ear, 3)

            # Draw eye landmarks
            for idx in LEFT_EYE + RIGHT_EYE:
                lm = landmarks[idx]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(result["frame"], (cx, cy), 2, (0, 255, 0), -1)

            # Draw eye outline
            for eye_pts_idx in [LEFT_EYE, RIGHT_EYE]:
                pts = []
                for idx in eye_pts_idx:
                    lm = landmarks[idx]
                    pts.append([int(lm.x * w), int(lm.y * h)])
                pts = np.array(pts, dtype=np.int32)
                cv2.polylines(result["frame"], [pts], True, (0, 255, 0), 1)

            if ear < EAR_THRESHOLD:
                self.frame_counter += 1
                progress = min(self.frame_counter / EAR_CONSEC_FRAMES, 1.0)
                bar_w    = int(300 * progress)
                cv2.rectangle(result["frame"], (10, 155), (310, 175), (50, 50, 50), -1)
                color = (0, 165, 255) if progress < 0.7 else (0, 0, 255)
                cv2.rectangle(result["frame"], (10, 155), (10 + bar_w, 175), color, -1)
                cv2.putText(result["frame"], "Drowsiness meter:", (10, 150),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                if self.frame_counter >= EAR_CONSEC_FRAMES:
                    result["alert"] = True
                    self.total_alerts += 1
                    cv2.rectangle(result["frame"], (0, 0), (640, 45), (0, 0, 180), -1)
                    cv2.putText(result["frame"], "!! DROWSINESS ALERT !!",
                                (30, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            else:
                self.frame_counter   = 0
                self.alert_triggered = False

            cv2.putText(result["frame"], f"EAR: {ear:.3f}", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
            cv2.putText(result["frame"], f"Threshold: {EAR_THRESHOLD}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            cv2.putText(result["frame"], f"Frames: {self.frame_counter}/{EAR_CONSEC_FRAMES}",
                        (10, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            cv2.putText(result["frame"], f"L:{left_ear:.2f} R:{right_ear:.2f}",
                        (10, 138), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            result["frame_counter"] = self.frame_counter

        else:
            cv2.putText(result["frame"], "No face detected", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            self.frame_counter = 0

        return result

    def reset(self):
        self.frame_counter   = 0
        self.alert_triggered = False