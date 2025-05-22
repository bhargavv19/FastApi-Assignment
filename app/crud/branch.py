from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.chat import Message
from app.schemas.chat import MessageCreate
import uuid

async def create_branch(
    db: Session,
    chat_id: uuid.UUID,
    parent_message_id: uuid.UUID,
    content: str,
    sender_id: uuid.UUID
) -> Message:
    # Get parent message
    parent_message = db.query(Message).filter(
        Message.id == parent_message_id,
        Message.chat_id == chat_id
    ).first()
    
    if not parent_message:
        raise ValueError("Parent message not found")
    
    # Calculate new branch path and level
    new_level = parent_message.branch_level + 1
    new_path = f"{parent_message.branch_path}.{new_level}" if parent_message.branch_path else str(new_level)
    
    # Create new message
    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        parent_message_id=parent_message_id,
        content=content,
        branch_level=new_level,
        branch_path=new_path,
        is_branch_root=True
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

async def get_branch_tree(
    db: Session,
    chat_id: uuid.UUID,
    message_id: uuid.UUID
) -> List[Message]:
    """Get all messages in a branch tree."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    
    if not message:
        return []
    
    # Get all messages in the same branch path
    branch_messages = db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.branch_path.like(f"{message.branch_path}%")
    ).order_by(Message.branch_path, Message.created_at).all()
    
    return branch_messages

async def get_active_branches(
    db: Session,
    chat_id: uuid.UUID
) -> List[Message]:
    """Get all active branch roots in a chat."""
    return db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.is_branch_root == True
    ).order_by(Message.created_at).all()

async def get_message_thread(
    db: Session,
    chat_id: uuid.UUID,
    message_id: uuid.UUID
) -> Tuple[Message, List[Message]]:
    """Get a message and its entire thread (parent and children)."""
    message = db.query(Message).filter(
        Message.id == message_id,
        Message.chat_id == chat_id
    ).first()
    
    if not message:
        return None, []
    
    # Get all messages in the thread
    thread_messages = db.query(Message).filter(
        Message.chat_id == chat_id,
        Message.branch_path.like(f"{message.branch_path}%")
    ).order_by(Message.branch_path, Message.created_at).all()
    
    return message, thread_messages 