from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Room, RoomMember
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
rooms_router = APIRouter(prefix="/rooms", tags=["rooms"])


# ── Request / Response schemas ──
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class CreateRoomRequest(BaseModel):
    name: str
    created_by: int | None = None  # user id of the creator (optional if JWT is used)


# ── Register ──
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Check if username or email already taken
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})
    return AuthResponse(access_token=token, username=user.username)


# ── Login ──
@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return AuthResponse(access_token=token, username=user.username)


# ── Room logic helpers ──
def _create_room_logic(body: CreateRoomRequest, db: Session, user_id: int | None = None):
    room_name = body.name.strip()
    if not room_name:
        raise HTTPException(status_code=400, detail="Room name cannot be empty")

    if db.query(Room).filter(Room.name == room_name).first():
        raise HTTPException(status_code=400, detail="Room name already taken")

    creator_id = user_id or body.created_by
    if not creator_id:
        raise HTTPException(status_code=400, detail="Creator ID is required")

    creator = db.query(User).filter(User.id == creator_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail="User not found")

    room = Room(name=room_name, created_by=creator_id)
    db.add(room)
    db.commit()
    db.refresh(room)

    member = RoomMember(user_id=creator_id, room_id=room.id)
    db.add(member)
    db.commit()

    return {"message": f"Room '{room.name}' created", "room_id": room.id, "name": room.name}


def _join_room_logic(room_id: int, user_id: int, db: Session):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(RoomMember).filter(
        RoomMember.user_id == user_id,
        RoomMember.room_id == room_id
    ).first()
    if existing:
        return {"message": f"User '{user.username}' is already a member of room '{room.name}'", "room_id": room.id}

    member = RoomMember(user_id=user_id, room_id=room.id)
    db.add(member)
    db.commit()

    return {"message": f"User '{user.username}' joined room '{room.name}'", "room_id": room.id}


# ── Room Endpoints (Dedicated /rooms prefix) ──
@rooms_router.get("")
@rooms_router.get("/")
def list_rooms(db: Session = Depends(get_db)):
    """List all available rooms with their member count."""
    rooms = db.query(Room).order_by(Room.id.asc()).all()
    result = []
    for r in rooms:
        member_count = db.query(RoomMember).filter(RoomMember.room_id == r.id).count()
        result.append({
            "id": r.id,
            "name": r.name,
            "created_by": r.created_by,
            "member_count": member_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


@rooms_router.post("", status_code=status.HTTP_201_CREATED)
@rooms_router.post("/create", status_code=status.HTTP_201_CREATED)
def create_room(
    body: CreateRoomRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _create_room_logic(body, db, user_id=current_user.id)


@rooms_router.post("/{room_id}/join")
def join_room(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _join_room_logic(room_id, current_user.id, db)


# ── Backward-compatible /auth/rooms routes ──
@router.post("/rooms/create", status_code=status.HTTP_201_CREATED)
def auth_create_room(body: CreateRoomRequest, db: Session = Depends(get_db)):
    return _create_room_logic(body, db, user_id=body.created_by)


@router.post("/rooms/{room_id}/join")
def auth_join_room(room_id: int, user_id: int, db: Session = Depends(get_db)):
    return _join_room_logic(room_id, user_id, db)
