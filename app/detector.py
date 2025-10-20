import time, threading
from collections import deque
from typing import Optional

import cv2, numpy as np
from .settings import settings
from .models import state
from .events import register_accept

class Detector:
    """Background thread that reads frames, runs ROI motion detection, and emits events."""
    def __init__(self, cap):
        self.cap = cap
        self.bg: Optional[np.ndarray] = None
        self.mog2 = None
        self.last_count_time = 0.0
        self.frame_buf = deque(maxlen=1)
        self.debug_last_thresh = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    @staticmethod
    def circular_mask(shape_or_img, cx, cy, r):
        if isinstance(shape_or_img, tuple):
            h, w = shape_or_img[:2]
        else:
            h, w = shape_or_img.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)
        return mask

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _loop(self):
        ok, frame = self.cap.read()
        if not ok:
            print("[FATAL] Camera not available")
            return

        mask = self.circular_mask(frame, settings.ROI_CX, settings.ROI_CY, settings.ROI_R)

        g0 = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        g0 = cv2.GaussianBlur(g0, (21, 21), 0)
        self.bg = g0.copy()

        self.mog2 = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=16, detectShadows=False
        ) if settings.USE_MOG2 else None

        consec_hot = 0
        last_idle_reseed = time.time()

        while not self._stop.is_set():
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.02)
                continue

            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            g = cv2.GaussianBlur(g, (21, 21), 0)

            if settings.USE_MOG2 and self.mog2 is not None:
                fgmask = self.mog2.apply(g)
                fgmask = cv2.bitwise_and(fgmask, fgmask, mask=mask)
                thresh = cv2.threshold(fgmask, 127, 255, cv2.THRESH_BINARY)[1]
            else:
                delta = cv2.absdiff(self.bg, g)
                delta_roi = cv2.bitwise_and(delta, delta, mask=mask)
                thresh = cv2.threshold(delta_roi, settings.DIFF_THRESH, 255, cv2.THRESH_BINARY)[1]
                self.bg = cv2.addWeighted(g, settings.BG_LEARN_RATE, self.bg, 1.0 - settings.BG_LEARN_RATE, 0)

            # Clean small speckles
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
            thresh = cv2.dilate(thresh, None, iterations=1)

            hot_pixels = int(np.sum(thresh == 255))
            self.debug_last_thresh = thresh
            now = time.time()

            # Auto-reseed background if quiet for a while
            if hot_pixels < (settings.MOTION_PIXELS_THRESHOLD // 2):
                if (now - last_idle_reseed) > settings.IDLE_RESET_SECONDS:
                    if settings.USE_MOG2:
                        self.mog2 = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=16, detectShadows=False)
                    else:
                        self.bg = g.copy()
                    consec_hot = 0
                    last_idle_reseed = now

            # Count consecutive frames above threshold
            if hot_pixels >= settings.MOTION_PIXELS_THRESHOLD:
                consec_hot += 1
            else:
                consec_hot = 0

            # Trigger accept if sustained and cooldown passed
            if consec_hot >= settings.CONSEC_FRAMES_REQUIRED and (now - self.last_count_time) >= settings.DETECT_COOLDOWN_S:
                register_accept(source="auto")
                self.last_count_time = now
                consec_hot = 0

            # HUD overlay for tooling & store latest frame
            cv2.circle(frame, (settings.ROI_CX, settings.ROI_CY), settings.ROI_R, (0,255,0), 2)
            # cv2.putText(frame, f"ROI hot: {hot_pixels}", (10, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(frame, f"Status: {state.message}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            # cv2.putText(frame, f"Points: {state.points}", (10, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

            self.frame_buf.append(frame)
            time.sleep(0.01)
