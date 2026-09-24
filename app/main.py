from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.database import engine
from app.models import Base
from app.connection_manager import ConnectionManager

Base.metadata.create_all(bind=engine)

app = FastAPI()
manager = ConnectionManager()


@app.get("/")
def root():
    return {"message": "Chat server is running"}


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket)
    await manager.broadcast(f"🟢 {username} joined the chat!")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"🔴 {username} left the chat.")