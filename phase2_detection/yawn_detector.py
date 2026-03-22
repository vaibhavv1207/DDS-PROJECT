# phase2_detection/yawn_detector.py
# ─────────────────────────────────────────
#  Yawn Detection using Mouth Aspect Ratio
#  MAR > threshold = yawning detected
# ─────────────────────────────────────────

import cv2
import numpy as np
from scipy.spatial import distance as dist
import os
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────
MAR_THRESHOLD      = float(os.getenv("MAR_THRESHOLD", 0.6))
YAWN_CONSEC_FRAMES = int(os.getenv("YAWN_CONSEC_FRAMES", 15))

# ── MediaPipe mouth landmark indices ─────
# Outer lips: top=13, bottom=14, left=61, right=291
# Inner lips: top=12, bottom=15, left=78, right=308
MOUTH_OUTER = [61, 13, 291, 14]   # left, top, right, bottom
MOUTH_INNER = [78, 12, 308, 15]


def mouth_aspect_ratio(landmarks, w, h):
    """
    Calculate Mouth Aspect Ratio (MAR).
    MAR = vertical distance / horizontal distance
    Mouth closed → MAR ~0.2
    Mouth open (yawn) → MAR > 0.6
    """
    # Outer mouth points
    left   = landmarks[61]
    right  = landmarks[291]
    top    = landmarks[13]
    bottom = landmarks[14]

    # Convert to pixel coords
    left_pt   = (left.x   * w, left.y   * h)
    right_pt  = (right.x  * w, right.y  * h)
    top_pt    = (top.x    * w, top.y    * h)
    bottom_pt = (bottom.x * w, bottom.y * h)

    vertical   = dist.euclidean(top_pt,  bottom_pt)
    horizontal = dist.euclidean(left_pt, right_pt)

    if horizontal == 0:
        return 0.0
    return round(vertical / horizontal, 3)


class YawnDetector:
    """
    Detects yawning using Mouth Aspect Ratio.
    Plug into main loop alongside DrowsinessDetector.
    """

    def __init__(self):
        self.frame_counter = 0
        self.yawn_count    = 0
        self.is_yawning    = False
        print(f"[INFO] YawnDetector ready. MAR threshold: {MAR_THRESHOLD}")

    def process(self, landmarks, frame, w, h):
        """
        Process landmarks for yawn detection.
        Returns dict with mar, yawning flag, yawn_count, annotated frame.
        """
        result = {
            "mar"     : 0.0,
            "yawning" : False,
            "yawn_count": self.yawn_count,
            "frame"   : frame,
        }

        try:
            mar = mouth_aspect_ratio(landmarks, w, h)
            result["mar"] = mar

            # Draw mouth outline
            mouth_pts = []
            for idx in [61, 185, 40, 39, 37, 0, 267, 269, 270, 409,
                        291, 375, 321, 405, 314, 17, 84, 181, 91, 146]:
                lm = landmarks[idx]
                mouth_pts.append([int(lm.x * w), int(lm.y * h)])
            mouth_pts = np.array(mouth_pts, dtype=np.int32)
            cv2.polylines(frame, [mouth_pts], True, (0, 165, 255), 1)

            # MAR threshold check
            if mar > MAR_THRESHOLD:
                self.frame_counter += 1
                if self.frame_counter >= YAWN_CONSEC_FRAMES:
                    self.is_yawning    = True
                    result["yawning"]  = True
                    if self.frame_counter == YAWN_CONSEC_FRAMES:
                        self.yawn_count += 1  # count each yawn once
                    result["yawn_count"] = self.yawn_count

                    # Yawn alert on frame
                    cv2.putText(frame, "YAWN DETECTED!", (10, 200),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
            else:
                self.frame_counter = 0
                self.is_yawning    = False

            # HUD
            color = (0, 165, 255) if mar > MAR_THRESHOLD else (200, 200, 200)
            cv2.putText(frame, f"MAR: {mar:.3f}", (400, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            cv2.putText(frame, f"Yawns: {self.yawn_count}", (400, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        except Exception as e:
            pass  # landmarks may not be fully visible

        return result

    def reset(self):
        self.frame_counter = 0
        self.yawn_count    = 0
        self.is_yawning    = False