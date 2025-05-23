from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, chat, websocket

api_router = APIRouter()
 
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chats", tags=["chats"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"]) 