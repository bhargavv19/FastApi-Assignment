from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud
from app.api import deps
from app.schemas.chat import Chat, ChatCreate, ChatUpdate, Message, MessageCreate, MessageUpdate
from app.models.chat import Chat as ChatModel, chat_participants
from app.models.message import Message as MessageModel

router = APIRouter()

@router.post("/", response_model=Chat)
async def create_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_in: ChatCreate,
    current_user = Depends(deps.get_current_user)
) -> Chat:
    """
    Create new chat.
    """
    try:
        chat = await crud.chat["create_chat"](db=db, chat_in=chat_in, current_user_id=current_user.id)
        return chat
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Chat])
async def read_chats(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_user)
) -> List[Chat]:
    """
    Retrieve chats.
    """
    created_chats, participated_chats = await crud.chat["get_user_chats"](
        db=db, current_user_id=current_user.id, skip=skip, limit=limit
    )
    return created_chats + participated_chats

@router.get("/{chat_id}", response_model=Chat)
async def read_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> Chat:
    """
    Get chat by ID.
    """
    # First check if chat exists
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail=f"Chat with ID {chat_id} not found")
    
    # Then check if user is a participant
    participant = db.execute(
        chat_participants.select().where(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == current_user.id
        )
    ).first()
    
    if not participant:
        # Try to fix participant status
        fixed = await crud.chat["fix_chat_participant_status"](
            db=db,
            chat_id=chat_id,
            user_id=current_user.id
        )
        if not fixed:
            raise HTTPException(
                status_code=403,
                detail=f"User {current_user.id} is not a participant in chat {chat_id}"
            )
    
    if chat.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Chat {chat_id} has been deleted"
        )
    
    return chat

@router.put("/{chat_id}", response_model=Chat)
async def update_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    chat_in: ChatUpdate,
    current_user = Depends(deps.get_current_user)
) -> Chat:
    """
    Update chat.
    """
    chat = await crud.chat["update_chat"](
        db=db, chat_id=chat_id, chat_in=chat_in, current_user_id=current_user.id
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.delete("/{chat_id}", response_model=Chat)
async def delete_chat(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> Chat:
    """
    Delete chat.
    """
    success = await crud.chat["delete_chat"](db=db, chat_id=chat_id, current_user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}

@router.post("/{chat_id}/messages", response_model=Message)
async def create_message(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    message_in: MessageCreate,
    current_user = Depends(deps.get_current_user)
) -> Message:
    """
    Create new message.
    """
    # Check if user is participant
    participant = crud.chat["get_participant"](
        db=db, chat_id=chat_id, user_id=current_user.id
    )
    if not participant:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Validate parent message if provided
    parent_message_id = message_in.parent_message_id
    if parent_message_id:
        parent_message = db.query(MessageModel).filter(
            MessageModel.id == parent_message_id,
            MessageModel.chat_id == chat_id
        ).first()
        if not parent_message:
            raise HTTPException(
                status_code=404,
                detail=f"Parent message {parent_message_id} not found in chat {chat_id}"
            )
    
    # Create message with sender_id
    message_data = message_in.model_dump(exclude_unset=True)  # Only include fields that were set
    message_data["sender_id"] = current_user.id
    message_data["chat_id"] = chat_id
    
    # Create message using the SQLAlchemy model
    message = MessageModel(
        content=message_data["content"],
        message_type=message_data["message_type"],
        chat_id=message_data["chat_id"],
        sender_id=message_data["sender_id"],
        parent_message_id=message_data.get("parent_message_id")  # This will be None if not provided
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@router.get("/{chat_id}/participants", response_model=List[dict])
async def get_chat_participants(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> List[dict]:
    """
    Get chat participants.
    """
    # First check if chat exists
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
    
    # Get all participants
    participants = db.execute(
        chat_participants.select().where(chat_participants.c.chat_id == chat_id)
    ).fetchall()
    
    # Convert to list of dicts
    return [dict(p._mapping) for p in participants]

@router.get("/{chat_id}/messages", response_model=List[Message])
async def read_messages(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(deps.get_current_user)
) -> List[Message]:
    """
    Retrieve messages.
    """
    # First check if chat exists
    chat = db.query(ChatModel).filter(ChatModel.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
    
    # Check if user is participant
    participant = crud.chat["get_participant"](
        db=db, chat_id=chat_id, user_id=current_user.id
    )
    if not participant:
        # Try to fix participant status
        fixed = await crud.chat["fix_chat_participant_status"](
            db=db,
            chat_id=chat_id,
            user_id=current_user.id
        )
        if not fixed:
            raise HTTPException(
                status_code=403,
                detail=f"User {current_user.id} is not a participant in chat {chat_id}"
            )
    
    # Get messages
    messages = db.query(MessageModel).filter(
        MessageModel.chat_id == chat_id,
        MessageModel.deleted_at.is_(None)
    ).order_by(MessageModel.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages

@router.put("/{chat_id}/messages/{message_id}", response_model=Message)
async def update_message(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    message_id: UUID,
    message_in: MessageUpdate,
    current_user = Depends(deps.get_current_user)
) -> Message:
    """
    Update message.
    """
    message = crud.message.get(db=db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    message = crud.message.update(db=db, db_obj=message, obj_in=message_in)
    return message

@router.delete("/{chat_id}/messages/{message_id}", response_model=Message)
async def delete_message(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    message_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> Message:
    """
    Delete message.
    """
    message = crud.message.get(db=db, id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    message = crud.message.remove(db=db, id=message_id)
    return message

@router.get("/{chat_id}/messages/{message_id}/thread", response_model=List[Message])
async def get_message_thread(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    message_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> List[Message]:
    """
    Get a message and its entire thread (parent and replies).
    """
    # Check if user is participant
    participant = crud.chat["get_participant"](
        db=db, chat_id=chat_id, user_id=current_user.id
    )
    if not participant:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the message
    message = db.query(MessageModel).filter(
        MessageModel.id == message_id,
        MessageModel.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get all messages in the thread
    thread_messages = db.query(MessageModel).filter(
        MessageModel.chat_id == chat_id,
        MessageModel.parent_message_id == message_id
    ).order_by(MessageModel.created_at).all()
    
    # Add the parent message to the beginning of the list
    return [message] + thread_messages

@router.get("/{chat_id}/branches", response_model=List[Message])
async def get_chat_branches(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> List[Message]:
    """
    Get all root messages (messages without parents) in a chat.
    """
    # Check if user is participant
    participant = crud.chat["get_participant"](
        db=db, chat_id=chat_id, user_id=current_user.id
    )
    if not participant:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get all root messages
    root_messages = db.query(MessageModel).filter(
        MessageModel.chat_id == chat_id,
        MessageModel.parent_message_id.is_(None),
        MessageModel.deleted_at.is_(None)
    ).order_by(MessageModel.created_at.desc()).all()
    
    return root_messages

@router.get("/{chat_id}/messages/{message_id}/branch", response_model=List[Message])
async def get_message_branch(
    *,
    db: Session = Depends(deps.get_db),
    chat_id: UUID,
    message_id: UUID,
    current_user = Depends(deps.get_current_user)
) -> List[Message]:
    """
    Get a message and all its replies in a branch.
    """
    # Check if user is participant
    participant = crud.chat["get_participant"](
        db=db, chat_id=chat_id, user_id=current_user.id
    )
    if not participant:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the message
    message = db.query(MessageModel).filter(
        MessageModel.id == message_id,
        MessageModel.chat_id == chat_id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get all messages in the branch
    branch_messages = db.query(MessageModel).filter(
        MessageModel.chat_id == chat_id,
        MessageModel.parent_message_id == message_id
    ).order_by(MessageModel.created_at).all()
    
    # Add the parent message to the beginning of the list
    return [message] + branch_messages 