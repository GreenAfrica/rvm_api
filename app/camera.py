import cv2
from .settings import settings

def open_camera():
    cap = cv2.VideoCapture(settings.CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_H)
    _lock_camera_params(cap)
    return cap

def _lock_camera_params(cap):
    # Best-effort – safe if unsupported by device.
    try:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)  # manual on many UVC cams
    except:
        pass
    for val in [50, 100, 200, 400]:
        if cap.set(cv2.CAP_PROP_EXPOSURE, float(val)):
            break
    try:
        cap.set(cv2.CAP_PROP_AUTO_WB, 0)
    except:
        pass
    for val in [4200, 4500, 5000]:
        if cap.set(cv2.CAP_PROP_WB_TEMPERATURE, float(val)):
            break
