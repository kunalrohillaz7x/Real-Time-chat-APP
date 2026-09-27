from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # List of all currently connected WebSocket clients
        self.active_connections: list[WebSocket] = []
        # Mapping of room_id -> list of connected WebSockets
        self.room_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int | None = None):
        """Accept a new connection and track it."""
        await websocket.accept()
        self.active_connections.append(websocket)
        if room_id is not None:
            if room_id not in self.room_connections:
                self.room_connections[room_id] = []
            self.room_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int | None = None):
        """Safely remove a connection from lists."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if room_id is not None and room_id in self.room_connections:
            if websocket in self.room_connections[room_id]:
                self.room_connections[room_id].remove(websocket)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        else:
            # If room_id was not passed, clean up from all rooms
            for rid, conns in list(self.room_connections.items()):
                if websocket in conns:
                    conns.remove(websocket)
                if not conns:
                    del self.room_connections[rid]

    async def broadcast(self, message: str, room_id: int | None = None):
        """Send a message to clients in a room or all clients if no room is specified."""
        targets = (
            self.room_connections.get(room_id, [])
            if room_id is not None
            else self.active_connections
        )
        dead = []
        for connection in list(targets):
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)

        for conn in dead:
            self.disconnect(conn, room_id=room_id)
