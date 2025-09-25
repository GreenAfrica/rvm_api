import time, uuid, asyncio
from .models import state, event_lock, ws_clients

async def _broadcast(payload: dict):
    dead = []
    for ws in list(ws_clients):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.discard(ws)

def register_accept(source: str = "auto"):
    code = uuid.uuid4().hex[:8].upper()
    with event_lock:
        state.points += 1
        state.message = "Bottle accepted"
        state.last_event = time.strftime('%H:%M:%S')
        state.last_code = code
    asyncio.run(_broadcast({"type": "accept", "code": code, "points": state.points, "source": source}))

def register_reject(source: str = "auto"):
    with event_lock:
        state.message = "Rejected"
        state.last_event = time.strftime('%H:%M:%S')
    asyncio.run(_broadcast({"type": "reject", "source": source}))
