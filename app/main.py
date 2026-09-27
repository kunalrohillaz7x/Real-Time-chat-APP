from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, get_db
from app.models import Base, Message, User, Room
from app.connection_manager import ConnectionManager
from app.routes import router as auth_router, rooms_router
from app.auth import decode_access_token

Base.metadata.create_all(bind=engine)  # this creates all the tables in the database

app = FastAPI(title="Real-Time Chat API")
manager = ConnectionManager()

# Register routers
app.include_router(auth_router)
app.include_router(rooms_router)

# Allow React dev server to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Chat server is running"}


# ── Chat history endpoints ──
@app.get("/messages")
@app.get("/rooms/{room_id}/messages")
def get_messages(room_id: int | None = None, limit: int = 50, db: Session = Depends(get_db)):
    """Return the most recent messages, oldest first. Optionally filtered by room_id."""
    query = db.query(Message)
    if room_id is not None:
        query = query.filter(Message.room_id == room_id)

    rows = (
        query
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # oldest first for display
    return [
        {
            "id": msg.id,
            "sender": msg.sender_username,
            "content": msg.content,
            "room_id": msg.room_id,
            "timestamp": msg.created_at.isoformat() if msg.created_at else None,
        }
        for msg in rows
    ]


async def handle_websocket_connection(
    websocket: WebSocket,
    token: str,
    room_id: int | None = None,
):
    # Verify JWT before accepting connection
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    username = payload["sub"]

    # Look up user in DB to get sender_id
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        await websocket.close(code=4001, reason="User not found")
        return

    # If room_id specified, check if room exists
    if room_id is not None:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            db.close()
            await websocket.close(code=4004, reason="Room not found")
            return

    await manager.connect(websocket, room_id=room_id)
    await manager.broadcast(f"🟢 {username} joined the chat!", room_id=room_id)
    try:
        while True:
            data = await websocket.receive_text()
            if not data or not data.strip():
                continue

            # ── Save message to database ──
            msg = Message(
                sender_id=user.id,
                sender_username=username,
                content=data.strip(),
                room_id=room_id,
            )
            db.add(msg)
            db.commit()

            await manager.broadcast(f"{username}: {data.strip()}", room_id=room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id=room_id)
        await manager.broadcast(f"🔴 {username} left the chat.", room_id=room_id)
    finally:
        db.close()


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    room_id: int | None = Query(None),
):
    await handle_websocket_connection(websocket, token, room_id=room_id)


@app.websocket("/ws/{room_id}")
async def websocket_room_endpoint(
    websocket: WebSocket,
    room_id: int,
    token: str = Query(...),
):
    await handle_websocket_connection(websocket, token, room_id=room_id)

