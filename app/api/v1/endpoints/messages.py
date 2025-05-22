from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.chat import MessageCreate, MessageResponse
from app.crud import chat as chat_crud
from app.core.cache import cache

router = APIRouter()

@router.post("/add-message", response_model=MessageResponse)
async def add_message(
    message_in: MessageCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Add a new message to a chat."""
    # Verify user has access to the chat
    chat = await chat_crud.get_chat(db, message_in.chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    
    message = await chat_crud.add_message(
        db=db,
        chat_id=message_in.chat_id,
        content=message_in.content,
        sender_id=current_user.id
    )
    return message

@router.get("/get-messages/{chat_id}", response_model=List[MessageResponse])
@cache(expire=60)
async def get_messages(
    chat_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get all messages in a chat."""
    # Verify user has access to the chat
    chat = await chat_crud.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    
    messages = await chat_crud.get_chat_messages(
        db=db,
        chat_id=chat_id,
        current_user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return messages 