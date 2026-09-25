from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.connection_manager import ConnectionManager
from app.routes import router as auth_router
from app.auth import decode_access_token

Base.metadata.create_all(bind=engine)

app = FastAPI()
manager = ConnectionManager()

# Register auth routes
app.include_router(auth_router)

# Allow React dev server to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Chat server is running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Verify JWT before accepting connection
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    username = payload["sub"]
    await manager.connect(websocket)
    await manager.broadcast(f"🟢 {username} joined the chat!")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"🔴 {username} left the chat.")