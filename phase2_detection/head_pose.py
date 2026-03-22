# phase2_detection/head_pose.py
# ─────────────────────────────────────────
#  Head Pose Estimation
#  Detects forward nod and sideways tilt
#  Uses MediaPipe landmarks + solvePnP
# ─────────────────────────────────────────

import cv2
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────
NOD_THRESHOLD  = float(os.getenv("NOD_THRESHOLD",  15.0))  # degrees down
TILT_THRESHOLD = float(os.getenv("TILT_THRESHOLD", 20.0))  # degrees sideways

# ── 3D reference face model points ───────
# Standard 3D face model in object space
MODEL_POINTS = np.array([
    (0.0,    0.0,    0.0),    # Nose tip          – landmark 1
    (0.0,   -330.0, -65.0),   # Chin              – landmark 152
    (-225.0, 170.0, -135.0),  # Left eye corner   – landmark 33
    (225.0,  170.0, -135.0),  # Right eye corner  – landmark 263
    (-150.0, -150.0, -125.0), # Left mouth corner – landmark 61
    (150.0,  -150.0, -125.0), # Right mouth corner– landmark 291
], dtype=np.float64)

# Corresponding MediaPipe landmark indices
FACE_LANDMARK_IDS = [1, 152, 33, 263, 61, 291]


class HeadPoseDetector:
    """
    Estimates head pose (pitch/yaw/roll) from facial landmarks.
    Detects nodding (pitch) and tilting (roll).
    """

    def __init__(self):
        self.nod_counter    = 0
        self.nod_alert      = False
        self.pitch          = 0.0
        self.yaw            = 0.0
        self.roll           = 0.0
        print(f"[INFO] HeadPoseDetector ready. Nod: {NOD_THRESHOLD}° Tilt: {TILT_THRESHOLD}°")

    def _get_camera_matrix(self, w, h):
        """Build a simple camera matrix from frame dimensions."""
        focal_length = w
        center       = (w / 2, h / 2)
        return np.array([
            [focal_length, 0,            center[0]],
            [0,            focal_length, center[1]],
            [0,            0,            1         ]
        ], dtype=np.float64)

    def process(self, landmarks, frame, w, h):
        """
        Estimate head pose from MediaPipe landmarks.
        Returns dict with pitch, yaw, roll, nodding/tilting flags.
        """
        result = {
            "pitch"    : 0.0,
            "yaw"      : 0.0,
            "roll"     : 0.0,
            "nodding"  : False,
            "tilting"  : False,
            "frame"    : frame,
        }

        try:
            # Get 2D image points from landmarks
            image_points = []
            for idx in FACE_LANDMARK_IDS:
                lm = landmarks[idx]
                image_points.append((lm.x * w, lm.y * h))
            image_points = np.array(image_points, dtype=np.float64)

            # Camera internals
            camera_matrix = self._get_camera_matrix(w, h)
            dist_coeffs   = np.zeros((4, 1), dtype=np.float64)

            # Solve for rotation and translation
            success, rotation_vec, translation_vec = cv2.solvePnP(
                MODEL_POINTS, image_points,
                camera_matrix, dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )

            if not success:
                return result

            # Convert rotation vector to rotation matrix
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)

            # Get Euler angles (pitch, yaw, roll) in degrees
            proj_matrix = np.hstack((rotation_mat, translation_vec))
            _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(proj_matrix)

            pitch = float(euler[0])  # up/down nod
            yaw   = float(euler[1])  # left/right turn
            roll  = float(euler[2])  # sideways tilt

            result["pitch"] = round(pitch, 1)
            result["yaw"]   = round(yaw,   1)
            result["roll"]  = round(roll,  1)

            self.pitch = pitch
            self.yaw   = yaw
            self.roll  = roll

            # ── Nod detection (head drooping forward) ──
            if pitch > NOD_THRESHOLD:
                self.nod_counter += 1
                if self.nod_counter >= 10:
                    result["nodding"] = True
                    cv2.putText(frame, "HEAD NOD DETECTED!", (10, 225),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            else:
                self.nod_counter = 0

            # ── Tilt detection (head leaning sideways) ──
            if abs(roll) > TILT_THRESHOLD:
                result["tilting"] = True
                cv2.putText(frame, "HEAD TILT DETECTED!", (10, 250),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)

            # ── Draw pose axes on nose tip ──────────────
            nose_tip = (int(landmarks[1].x * w), int(landmarks[1].y * h))

            # Project axes
            axis_pts = np.float32([
                [0, 0, 0], [50, 0, 0], [0, 50, 0], [0, 0, 50]
            ])
            img_pts, _ = cv2.projectPoints(
                axis_pts, rotation_vec, translation_vec,
                camera_matrix, dist_coeffs
            )
            img_pts = img_pts.astype(int)

            origin = tuple(img_pts[0].ravel())
            cv2.arrowedLine(frame, origin, tuple(img_pts[1].ravel()), (0, 0, 255),   2)  # X red
            cv2.arrowedLine(frame, origin, tuple(img_pts[2].ravel()), (0, 255, 0),   2)  # Y green
            cv2.arrowedLine(frame, origin, tuple(img_pts[3].ravel()), (255, 0, 0),   2)  # Z blue

            # ── HUD ──────────────────────────────────────
            cv2.putText(frame, f"Pitch:{pitch:+.1f}", (400, 115),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(frame, f"Yaw:{yaw:+.1f}",    (400, 135),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(frame, f"Roll:{roll:+.1f}",  (400, 155),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        except Exception as e:
            pass

        return result

    def reset(self):
        self.nod_counter = 0
        self.nod_alert   = False