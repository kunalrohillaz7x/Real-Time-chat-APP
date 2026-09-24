from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # List of all currently connected WebSocket clients
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept a new connection and add it to the list."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a connection from the list."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """Send a message to ALL connected clients."""
        for connection in self.active_connections:
            await connection.send_text(message)
