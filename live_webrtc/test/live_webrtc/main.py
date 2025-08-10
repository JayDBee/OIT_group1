from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio
import uuid

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Very simple in-memory room pairing: one waiting peer is stored.
WAITING = None

# Signaling endpoint
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    peer_id = str(uuid.uuid4())
    print("Peer connected:", peer_id)

    global WAITING
    try:
        # If no peer waiting, put this one as waiting and hold
        if WAITING is None:
            WAITING = {"ws": ws, "id": peer_id}
            await ws.send_json({"type": "waiting"})
            # Wait until disconnected (or second peer pairs)
            while True:
                msg = await ws.receive_text()  # keep connection open
        else:
            # pair with waiting peer
            peer = WAITING
            WAITING = None
            # notify both peers of pairing
            await peer["ws"].send_json({"type": "paired", "peer": peer_id})
            await ws.send_json({"type": "paired", "peer": peer["id"]})

            # now forward messages between ws and peer["ws"]
            async def forward(src: WebSocket, dst: WebSocket):
                try:
                    while True:
                        data = await src.receive_json()
                        await dst.send_json(data)
                except WebSocketDisconnect:
                    await dst.send_json({"type": "peer-disconnected"})
                except Exception:
                    pass

            # run both forwards concurrently
            await asyncio.gather(
                forward(ws, peer["ws"]),
                forward(peer["ws"], ws),
            )
    except WebSocketDisconnect:
        print("Peer disconnected:", peer_id)
        # If they were the waiting one, clear it
        if WAITING and WAITING.get("id") == peer_id:
            WAITING = None
    except Exception as e:
        print("WS error:", e)
        if WAITING and WAITING.get("id") == peer_id:
            WAITING = None