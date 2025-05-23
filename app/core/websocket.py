from typing import Dict, Set
from fastapi import WebSocket
import json
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[UUID, WebSocket] = {}
        # Store chat room connections
        self.chat_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def connect_to_chat(self, websocket: WebSocket, chat_id: UUID):
        await websocket.accept()
        if chat_id not in self.chat_connections:
            self.chat_connections[chat_id] = set()
        self.chat_connections[chat_id].add(websocket)

    async def disconnect_from_chat(self, websocket: WebSocket, chat_id: UUID):
        if chat_id in self.chat_connections:
            self.chat_connections[chat_id].remove(websocket)
            if not self.chat_connections[chat_id]:
                del self.chat_connections[chat_id]

    async def send_personal_message(self, message: dict, user_id: UUID):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

    async def broadcast_to_chat(self, message: dict, chat_id: UUID):
        if chat_id in self.chat_connections:
            for connection in self.chat_connections[chat_id]:
                await connection.send_json(message)

    async def broadcast_notification(self, message: dict, exclude_user_id: UUID = None):
        for user_id, connection in self.active_connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            await connection.send_json(message)

manager = ConnectionManager() 