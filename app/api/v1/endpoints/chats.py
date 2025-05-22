from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.chat import ChatCreate, ChatUpdate, ChatResponse
from app.crud import chat as chat_crud
from app.core.cache import cache

router = APIRouter()

@router.post("/create-chat", response_model=ChatResponse)
async def create_chat(
    chat_in: ChatCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create a new chat with participants."""
    try:
        chat = await chat_crud.create_chat(
            db=db,
            chat_in=chat_in,
            current_user_id=current_user.id
        )
        return chat
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/get-chat/{chat_id}", response_model=ChatResponse)
@cache(expire=60)
async def get_chat(
    chat_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get chat details and messages."""
    chat = await chat_crud.get_chat(
        db=db,
        chat_id=chat_id,
        current_user_id=current_user.id
    )
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    return chat

@router.get("/my-chats", response_model=Dict[str, List[ChatResponse]])
async def get_my_chats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get all chats for the current user, separated into created and participated."""
    created_chats, participated_chats = await chat_crud.get_user_chats(
        db=db,
        current_user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return {
        "created_chats": created_chats,
        "participated_chats": participated_chats
    }

@router.put("/update-chat/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    chat_in: ChatUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Update chat metadata and participants."""
    chat = await chat_crud.update_chat(
        db=db,
        chat_id=chat_id,
        chat_in=chat_in,
        current_user_id=current_user.id
    )
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    return chat

@router.delete("/delete-chat/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Soft delete a chat."""
    success = await chat_crud.delete_chat(
        db=db,
        chat_id=chat_id,
        current_user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    return None 