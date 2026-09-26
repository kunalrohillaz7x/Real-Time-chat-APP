from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, get_db
from app.models import Base, Message, User
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


# ── Chat history endpoint ──
@app.get("/messages")
def get_messages(limit: int = 50, db: Session = Depends(get_db)):
    """Return the most recent messages, oldest first."""
    rows = (
        db.query(Message)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()  # oldest first for display
    return [
        {
            "sender": msg.sender_username,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
        }
        for msg in rows
    ]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
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

    await manager.connect(websocket)
    await manager.broadcast(f"🟢 {username} joined the chat!")
    try:
        while True:
            data = await websocket.receive_text()

            # ── Save message to database ──
            msg = Message(
                sender_id=user.id,
                sender_username=username,
                content=data,
            )
            db.add(msg)
            db.commit()

            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"🔴 {username} left the chat.")
    finally:
        db.close()
