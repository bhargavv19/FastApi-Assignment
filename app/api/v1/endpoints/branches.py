from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.chat import MessageResponse
from app.crud import branch as branch_crud
from app.crud import chat as chat_crud
from app.core.cache import cache

router = APIRouter()

@router.post("/create-branch", response_model=MessageResponse)
async def create_branch(
    chat_id: str,
    parent_message_id: str,
    content: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Create a new branch from a message."""
    try:
        # Verify user has access to the chat
        chat = await chat_crud.get_chat(db, chat_id, current_user.id)
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found or you don't have access to it"
            )
        
        message = await branch_crud.create_branch(
            db=db,
            chat_id=chat_id,
            parent_message_id=parent_message_id,
            content=content,
            sender_id=current_user.id
        )
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/get-branch/{chat_id}/{message_id}", response_model=List[MessageResponse])
@cache(expire=60)
async def get_branch(
    chat_id: str,
    message_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get all messages in a branch."""
    # Verify user has access to the chat
    chat = await chat_crud.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    
    messages = await branch_crud.get_branch_tree(
        db=db,
        chat_id=chat_id,
        message_id=message_id
    )
    return messages

@router.get("/get-active-branches/{chat_id}", response_model=List[MessageResponse])
@cache(expire=60)
async def get_active_branches(
    chat_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get all active branch roots in a chat."""
    # Verify user has access to the chat
    chat = await chat_crud.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    
    branches = await branch_crud.get_active_branches(
        db=db,
        chat_id=chat_id
    )
    return branches

@router.get("/get-thread/{chat_id}/{message_id}", response_model=List[MessageResponse])
@cache(expire=60)
async def get_thread(
    chat_id: str,
    message_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """Get a message and its entire thread."""
    # Verify user has access to the chat
    chat = await chat_crud.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found or you don't have access to it"
        )
    
    message, thread_messages = await branch_crud.get_message_thread(
        db=db,
        chat_id=chat_id,
        message_id=message_id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return thread_messages 