from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.chat import Chat, chat_participants
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatUpdate, MessageCreate, MessageUpdate
from datetime import datetime
import uuid
import logging

from app.crud.base import CRUDBase

# Configure logging
logger = logging.getLogger(__name__)

class CRUDChat(CRUDBase[Chat, ChatCreate, ChatUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Chat]:
        return db.query(Chat).filter(Chat.name == name).first()

    def get_user_chats(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Chat]:
        return (
            db.query(Chat)
            .join(chat_participants)
            .filter(chat_participants.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_participant(
        self, db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[dict]:
        try:
            result = db.execute(
                chat_participants.select().where(
                    chat_participants.c.chat_id == chat_id,
                    chat_participants.c.user_id == user_id
                )
            ).first()
            
            if not result:
                return None
                
            # Convert Row to dict by accessing the _mapping attribute
            return dict(result._mapping)
        except Exception as e:
            logger.error(f"Error getting participant: {str(e)}", exc_info=True)
            raise

    def add_participant(
        self, db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID, role: str = "member"
    ) -> None:
        stmt = chat_participants.insert().values(
            chat_id=chat_id,
            user_id=user_id,
            role=role
        )
        db.execute(stmt)
        db.commit()

    def remove_participant(
        self, db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        stmt = chat_participants.delete().where(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == user_id
        )
        db.execute(stmt)
        db.commit()

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    def get_chat_messages(
        self, db: Session, *, chat_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_messages(
        self, db: Session, *, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        return (
            db.query(Message)
            .filter(Message.sender_id == user_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

chat = CRUDChat(Chat)
message = CRUDMessage(Message)

async def create_chat(db: Session, chat_in: ChatCreate, current_user_id: uuid.UUID) -> Chat:
    # Validate participants exist
    participants = db.query(User).filter(User.id.in_(chat_in.participant_ids)).all()
    if len(participants) != len(chat_in.participant_ids):
        raise ValueError("One or more participants not found")
    
    # Create chat
    chat = Chat(
        name=chat_in.name,
        type=chat_in.type,
        created_by=current_user_id
    )
    db.add(chat)
    db.flush()  # Flush to get the chat ID
    
    # Add participants
    for participant in participants:
        # Set role as 'admin' for chat creator, 'member' for others
        role = "admin" if participant.id == current_user_id else "member"
        db.execute(
            chat_participants.insert().values(
                chat_id=chat.id,
                user_id=participant.id,
                role=role
            )
        )
    
    db.commit()
    db.refresh(chat)
    return chat

async def get_chat(db: Session, chat_id: uuid.UUID, current_user_id: uuid.UUID) -> Optional[Chat]:
    # First check if chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        logger.info(f"Chat with ID {chat_id} not found")
        return None
    
    # Then check if user is a participant
    participant = db.execute(
        chat_participants.select().where(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == current_user_id
        )
    ).first()
    
    if not participant:
        logger.info(f"User {current_user_id} is not a participant in chat {chat_id}")
        return None
    
    if chat.deleted_at is not None:
        logger.info(f"Chat {chat_id} has been deleted")
        return None
    
    logger.info(f"Successfully retrieved chat {chat_id} for user {current_user_id}")
    return chat

async def update_chat(
    db: Session,
    chat_id: uuid.UUID,
    chat_in: ChatUpdate,
    current_user_id: uuid.UUID
) -> Optional[Chat]:
    chat = await get_chat(db, chat_id, current_user_id)
    if not chat:
        return None
    
    # Update basic fields
    update_data = chat_in.model_dump(exclude_unset=True, exclude={'participant_ids'})
    for field, value in update_data.items():
        setattr(chat, field, value)
    
    # Update participants if provided
    if chat_in.participant_ids is not None:
        # Remove existing participants
        db.execute(
            chat_participants.delete().where(chat_participants.c.chat_id == chat_id)
        )
        
        # Add new participants
        participants = db.query(User).filter(User.id.in_(chat_in.participant_ids)).all()
        for participant in participants:
            db.execute(
                chat_participants.insert().values(
                    chat_id=chat_id,
                    user_id=participant.id
                )
            )
    
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chat)
    return chat

async def delete_chat(db: Session, chat_id: uuid.UUID, current_user_id: uuid.UUID) -> bool:
    chat = await get_chat(db, chat_id, current_user_id)
    if not chat:
        return False
    
    chat.deleted_at = datetime.utcnow()
    db.commit()
    return True

async def get_user_chats(
    db: Session,
    current_user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Chat], List[Chat]]:
    """Get both created and participated chats for a user."""
    logger.info(f"Getting chats for user {current_user_id}")
    
    # Get created chats
    created_chats = db.query(Chat).filter(
        Chat.created_by == current_user_id,
        Chat.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()
    logger.info(f"Found {len(created_chats)} created chats")
    
    # Get participated chats (excluding created ones)
    participated_chats = db.query(Chat).join(
        chat_participants,
        Chat.id == chat_participants.c.chat_id
    ).filter(
        chat_participants.c.user_id == current_user_id,
        Chat.created_by != current_user_id,
        Chat.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()
    logger.info(f"Found {len(participated_chats)} participated chats")
    
    # Verify participant status for each chat
    for chat in created_chats + participated_chats:
        participant = db.execute(
            chat_participants.select().where(
                chat_participants.c.chat_id == chat.id,
                chat_participants.c.user_id == current_user_id
            )
        ).first()
        if not participant:
            logger.warning(f"User {current_user_id} is not a participant in chat {chat.id} but chat appears in their list")
    
    return created_chats, participated_chats

async def get_chat_messages(
    db: Session,
    chat_id: uuid.UUID,
    current_user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Message]:
    chat = await get_chat(db, chat_id, current_user_id)
    if not chat:
        return []
    
    return db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()

def get(db: Session, id: uuid.UUID) -> Optional[Chat]:
    return db.query(Chat).filter(Chat.id == id).first()

def get_multi(
    db: Session, *, skip: int = 0, limit: int = 100
) -> List[Chat]:
    return db.query(Chat).offset(skip).limit(limit).all()

def create(db: Session, *, obj_in: ChatCreate) -> Chat:
    try:
        logger.info(f"Creating chat with name: {obj_in.name}")
        db_obj = Chat(
            name=obj_in.name,
            description=obj_in.description,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(f"Chat created successfully with ID: {db_obj.id}")
        return db_obj
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}", exc_info=True)
        db.rollback()
        raise

def update(
    db: Session, *, db_obj: Chat, obj_in: ChatUpdate
) -> Chat:
    try:
        update_data = obj_in.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    except Exception as e:
        logger.error(f"Error updating chat: {str(e)}", exc_info=True)
        db.rollback()
        raise

def remove(db: Session, *, id: uuid.UUID) -> Chat:
    try:
        obj = db.query(Chat).get(id)
        db.delete(obj)
        db.commit()
        return obj
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}", exc_info=True)
        db.rollback()
        raise

def add_participant(
    db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID, role: str = "member"
) -> None:
    try:
        stmt = chat_participants.insert().values(
            chat_id=chat_id,
            user_id=user_id,
            role=role
        )
        db.execute(stmt)
        db.commit()
    except Exception as e:
        logger.error(f"Error adding participant: {str(e)}", exc_info=True)
        db.rollback()
        raise

def remove_participant(
    db: Session, *, chat_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    try:
        stmt = chat_participants.delete().where(
            chat_participants.c.chat_id == chat_id,
            chat_participants.c.user_id == user_id
        )
        db.execute(stmt)
        db.commit()
    except Exception as e:
        logger.error(f"Error removing participant: {str(e)}", exc_info=True)
        db.rollback()
        raise

async def fix_chat_participant_status(
    db: Session,
    chat_id: uuid.UUID,
    user_id: uuid.UUID
) -> bool:
    """Fix inconsistent chat participant status by adding user as participant if they should be."""
    try:
        # Check if chat exists and is not deleted
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.deleted_at.is_(None)
        ).first()
        
        if not chat:
            logger.warning(f"Chat {chat_id} not found or deleted")
            return False
            
        # Check if user is already a participant
        participant = db.execute(
            chat_participants.select().where(
                chat_participants.c.chat_id == chat_id,
                chat_participants.c.user_id == user_id
            )
        ).first()
        
        if participant:
            logger.info(f"User {user_id} is already a participant in chat {chat_id}")
            return True
            
        # Add user as participant with appropriate role
        role = "admin" if chat.created_by == user_id else "member"
        db.execute(
            chat_participants.insert().values(
                chat_id=chat_id,
                user_id=user_id,
                role=role
            )
        )
        db.commit()
        logger.info(f"Added user {user_id} as {role} to chat {chat_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing chat participant status: {str(e)}")
        db.rollback()
        return False 