# phase2_detection/perclos.py
# ─────────────────────────────────────────
#  PERCLOS Metric
#  Percentage of Eye Closure over time
#  Industry standard drowsiness measure
#  PERCLOS > 0.7 over 60s = high drowsiness
# ─────────────────────────────────────────

import time
from collections import deque
import cv2
import os
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────
PERCLOS_WINDOW   = int(os.getenv("PERCLOS_WINDOW",   60))   # seconds
PERCLOS_THRESHOLD = float(os.getenv("PERCLOS_THRESHOLD", 0.4))  # 40% closed = alert
EAR_CLOSED       = float(os.getenv("EAR_THRESHOLD",  0.25))  # same as EAR threshold


class PERCLOSTracker:
    """
    PERCLOS = Percentage of Eye Closure over a rolling time window.

    Tracks whether eyes are open/closed each frame.
    Calculates % of frames where eyes were closed over last N seconds.
    PERCLOS > 0.4 (40%) indicates significant drowsiness.
    """

    def __init__(self, window_seconds=None):
        self.window_seconds = window_seconds or PERCLOS_WINDOW
        # Store (timestamp, is_closed) tuples
        self._history = deque()
        self.perclos  = 0.0
        self.level    = "LOW"
        print(f"[INFO] PERCLOS tracker ready. Window: {self.window_seconds}s Threshold: {PERCLOS_THRESHOLD}")

    def update(self, ear):
        """
        Update PERCLOS with current EAR value.
        Call once per frame.
        Returns current PERCLOS score (0.0 to 1.0).
        """
        now       = time.time()
        is_closed = ear < EAR_CLOSED

        # Add current frame
        self._history.append((now, is_closed))

        # Remove entries older than window
        cutoff = now - self.window_seconds
        while self._history and self._history[0][0] < cutoff:
            self._history.popleft()

        # Calculate PERCLOS
        if len(self._history) == 0:
            self.perclos = 0.0
        else:
            closed_count = sum(1 for _, closed in self._history if closed)
            self.perclos = closed_count / len(self._history)

        # Determine level
        if self.perclos >= PERCLOS_THRESHOLD:
            self.level = "HIGH"
        elif self.perclos >= PERCLOS_THRESHOLD * 0.6:
            self.level = "MEDIUM"
        else:
            self.level = "LOW"

        return self.perclos

    def draw(self, frame):
        """Draw PERCLOS info on frame."""
        # Color based on level
        colors = {"LOW": (0, 255, 0), "MEDIUM": (0, 165, 255), "HIGH": (0, 0, 255)}
        color  = colors.get(self.level, (200, 200, 200))

        # PERCLOS bar (bottom right area)
        bar_x, bar_y = 400, 175
        bar_w = int(200 * self.perclos)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + 200, bar_y + 14), (50, 50, 50), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + 14), color, -1)

        cv2.putText(frame, f"PERCLOS: {self.perclos:.0%} [{self.level}]",
                    (bar_x, bar_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        samples = len(self._history)
        cv2.putText(frame, f"Samples: {samples}/{self.window_seconds}s",
                    (bar_x, bar_y + 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        # Alert if HIGH
        if self.level == "HIGH":
            cv2.putText(frame, "HIGH PERCLOS - VERY DROWSY!",
                        (10, 275),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame

    def reset(self):
        self._history.clear()
        self.perclos = 0.0
        self.level   = "LOW"