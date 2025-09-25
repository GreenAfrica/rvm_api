import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .models import state, ws_clients

router = APIRouter()

@router.websocket("/ws")
async def ws_events(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    # Send snapshot on connect
    await ws.send_json({
        "type": "hello",
        "points": state.points,
        "message": state.message,
        "last_code": state.last_code
    })
    try:
        while True:
            # Keepalive — allow client to send pings or ignore
            try:
                _ = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        ws_clients.discard(ws)
