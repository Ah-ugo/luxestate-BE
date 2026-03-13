from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        # A user can have multiple connections from different tabs/devices
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_email: str):
        await websocket.accept()
        if user_email not in self.active_connections:
            self.active_connections[user_email] = []
        self.active_connections[user_email].append(websocket)

    def disconnect(self, websocket: WebSocket, user_email: str):
        if user_email in self.active_connections:
            self.active_connections[user_email].remove(websocket)
            if not self.active_connections[user_email]:
                del self.active_connections[user_email]

    async def send_personal_message(self, message: dict, recipient_email: str):
        if recipient_email in self.active_connections:
            for websocket in self.active_connections[recipient_email]:
                await websocket.send_text(json.dumps(message))

    async def broadcast_to_admins(self, message: dict, admin_emails: List[str]):
        for admin_email in admin_emails:
            if admin_email in self.active_connections:
                for websocket in self.active_connections[admin_email]:
                    await websocket.send_text(json.dumps(message))

manager = ConnectionManager()