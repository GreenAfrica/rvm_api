from pydantic import BaseModel

class Settings(BaseModel):
    # Camera
    CAM_INDEX: int = 0
    FRAME_W: int = 640
    FRAME_H: int = 480

    # ROI (entry hole)
    ROI_CX: int = 310
    ROI_CY: int = 190
    ROI_R: int = 55

    # Detection thresholds
    USE_MOG2: bool = True
    MOTION_PIXELS_THRESHOLD: int = 1500
    CONSEC_FRAMES_REQUIRED: int = 5
    DETECT_COOLDOWN_S: float = 2.5

    # Absdiff background path
    DIFF_THRESH: int = 15
    BG_LEARN_RATE: float = 0.005
    IDLE_RESET_SECONDS: float = 10.0

    # JPEG quality for tooling images
    JPEG_QUALITY: int = 80

settings = Settings()
