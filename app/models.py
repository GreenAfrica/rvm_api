import threading
from typing import Optional, Set
from pydantic import BaseModel
from fastapi import WebSocket

class RvmState(BaseModel):
    message: str = "Ready"
    points: int = 0
    last_event: Optional[str] = None
    last_code: Optional[str] = None

state = RvmState()
event_lock = threading.Lock()

# WebSocket client registry
ws_clients: Set[WebSocket] = set()
