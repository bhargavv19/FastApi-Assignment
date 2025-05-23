from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import List
from uuid import UUID
from app.core.websocket import manager
from app.api import deps
from app import crud
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.mongodb.message import MongoMessage
from app.services.mongodb.message_service import message_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: UUID):
    """
    WebSocket endpoint for personal notifications and messages.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "direct_message":
                # Handle direct message
                message_data = data["data"]
                # Create message in MongoDB
                mongo_message = MongoMessage(
                    chat_id=message_data["chat_id"],
                    sender_id=user_id,
                    content=message_data["content"],
                    message_type=message_data["message_type"],
                    parent_message_id=message_data.get("parent_message_id"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                created_message = await message_service.create_message(mongo_message)
                
                # Send notification to recipient
                await manager.send_personal_message(
                    {
                        "type": "new_direct_message",
                        "data": created_message.model_dump()
                    },
                    message_data["recipient_id"]
                )
                
    except WebSocketDisconnect:
        await manager.disconnect(user_id)

@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    chat_id: UUID,
    db: Session = Depends(deps.get_db)
):
    """
    WebSocket endpoint for chat room messages.
    """
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for chat_id: {chat_id}")
        
        # Get current user from token
        try:
            current_user = await deps.get_current_user_ws(websocket, db)
            logger.info(f"User authenticated: {current_user.email}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Verify user is participant in chat
        try:
            participant = crud.chat["get_participant"](
                db=db, chat_id=chat_id, user_id=current_user.id
            )
            if not participant:
                logger.warning(f"User {current_user.email} is not a participant in chat {chat_id}")
                await websocket.close(code=4003, reason="Not enough permissions")
                return
            logger.info(f"User {current_user.email} verified as participant in chat {chat_id}")
        except Exception as e:
            logger.error(f"Error verifying chat participant: {str(e)}")
            await websocket.close(code=4000, reason="Error verifying chat participant")
            return

        await manager.connect_to_chat(websocket, chat_id)
        logger.info(f"User {current_user.email} connected to chat {chat_id}")
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data["type"] == "send_message":
                    # Handle chat message
                    message_data = data["data"]
                    
                    # Create message in MongoDB
                    mongo_message = MongoMessage(
                        chat_id=chat_id,
                        sender_id=current_user.id,
                        content=message_data["content"],
                        message_type=message_data["message_type"],
                        parent_message_id=message_data.get("parent_message_id"),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    created_message = await message_service.create_message(mongo_message)
                    
                    # Get sender information
                    sender = crud.user["get"](db=db, id=current_user.id)
                    if sender:
                        message_dict = created_message.model_dump()
                        message_dict["sender"] = {
                            "id": str(sender.id),
                            "username": sender.username,
                            "email": sender.email,
                            "is_active": sender.is_active,
                            "created_at": sender.created_at
                        }
                        
                        # Broadcast to all chat participants
                        await manager.broadcast_to_chat(
                            {
                                "type": "new_message",
                                "data": message_dict
                            },
                            chat_id
                        )
                        logger.info(f"Message broadcasted in chat {chat_id}")
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Error processing message"}
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for chat {chat_id}")
        await manager.disconnect_from_chat(websocket, chat_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass 