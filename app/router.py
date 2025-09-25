from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from typing import Optional
import io, qrcode, cv2

from .models import state, event_lock
from .events import register_accept, register_reject
from .settings import settings
from .factory import detector

router = APIRouter()

# -------------------- Status --------------------
class StatusOut(BaseModel):
    message: str
    points: int
    last_event: Optional[str] = None
    last_code: Optional[str] = None

@router.get("/status", response_model=StatusOut)
def get_status():
    with event_lock:
        return StatusOut(**state.model_dump())


# -------------------- Control --------------------
@router.post("/event/accept")
def accept_event():
    register_accept(source="manual")
    return {"ok": True, "code": state.last_code, "points": state.points}

@router.post("/event/reject")
def reject_event():
    register_reject(source="manual")
    return {"ok": True}

@router.get("/qr.png")
def qr_png(code: Optional[str] = None):
    code = code or state.last_code or "NO-CODE"
    img = qrcode.make(f"RVM:{code}")
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

@router.post("/reset")
def reset_status():
    """Reset points, message, and last event/code back to initial state."""
    with event_lock:
        state.points = 0
        state.message = "Ready"
        state.last_event = None
        state.last_code = None
    return {"ok": True, "message": "State reset", "points": state.points}
    

# -------------------- Config --------------------
class ConfigOut(BaseModel):
    ROI_CX: int; ROI_CY: int; ROI_R: int
    USE_MOG2: bool
    MOTION_PIXELS_THRESHOLD: int
    CONSEC_FRAMES_REQUIRED: int
    DETECT_COOLDOWN_S: float
    DIFF_THRESH: int
    BG_LEARN_RATE: float
    IDLE_RESET_SECONDS: float

class SetRoiIn(BaseModel):
    cx: int; cy: int; r: int

@router.get("/config", response_model=ConfigOut)
def read_config():
    return ConfigOut(
        ROI_CX=settings.ROI_CX, ROI_CY=settings.ROI_CY, ROI_R=settings.ROI_R,
        USE_MOG2=settings.USE_MOG2,
        MOTION_PIXELS_THRESHOLD=settings.MOTION_PIXELS_THRESHOLD,
        CONSEC_FRAMES_REQUIRED=settings.CONSEC_FRAMES_REQUIRED,
        DETECT_COOLDOWN_S=settings.DETECT_COOLDOWN_S,
        DIFF_THRESH=settings.DIFF_THRESH,
        BG_LEARN_RATE=settings.BG_LEARN_RATE,
        IDLE_RESET_SECONDS=settings.IDLE_RESET_SECONDS,
    )

@router.post("/config/roi", response_model=ConfigOut)
def set_roi(body: SetRoiIn):
    settings.ROI_CX = int(body.cx)
    settings.ROI_CY = int(body.cy)
    settings.ROI_R = int(body.r)
    return read_config()

@router.post("/reseed")
def reseed_background():
    ok, frame = detector.cap.read()
    if not ok:
        raise HTTPException(status_code=503, detail="Camera unavailable")
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (21, 21), 0)
    detector.bg = g.copy()
    if settings.USE_MOG2:
        detector.mog2 = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=16, detectShadows=False
        )
    return {"ok": True}


# -------------------- Debug / Tooling --------------------
@router.get("/frame.jpg")
def latest_frame():
    frame = detector.frame_buf[-1] if detector.frame_buf else None
    if frame is None:
        ok, frame = detector.cap.read()
        if not ok:
            raise HTTPException(status_code=503, detail="No frame")
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), settings.JPEG_QUALITY])
    if not ok:
        raise HTTPException(status_code=500, detail="Encode error")
    return Response(content=buf.tobytes(), media_type="image/jpeg")

@router.get("/frame/overlay.jpg")
def overlay_preview():
    ok, frame = detector.cap.read()
    if not ok:
        raise HTTPException(status_code=503, detail="No frame")
    cv2.circle(frame, (settings.ROI_CX, settings.ROI_CY), settings.ROI_R, (0,255,0), 2)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise HTTPException(status_code=500, detail="Encode error")
    return Response(content=buf.tobytes(), media_type="image/jpeg")

@router.get("/debug/binary.jpg")
def debug_binary():
    img = detector.debug_last_thresh
    if img is None:
        raise HTTPException(status_code=503, detail="No debug frame")
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise HTTPException(status_code=500, detail="Encode error")
    return Response(content=buf.tobytes(), media_type="image/jpeg")
