from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, UUID4, EmailStr, validator
import uuid

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserResponse(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    name: str
    type: str  # 'direct' or 'group'
    is_active: bool = True

class ChatCreate(ChatBase):
    participant_ids: List[uuid.UUID]

class ChatUpdate(ChatBase):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    participant_ids: Optional[List[uuid.UUID]] = None

class ChatInDBBase(ChatBase):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Chat(ChatInDBBase):
    pass

class MessageBase(BaseModel):
    content: str
    message_type: str  # 'text', 'image', 'file', etc.
    parent_message_id: Optional[uuid.UUID] = None

class MessageCreate(MessageBase):
    chat_id: uuid.UUID

class MessageUpdate(MessageBase):
    content: Optional[str] = None
    message_type: Optional[str] = None

class MessageInDBBase(MessageBase):
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Message(MessageInDBBase):
    sender: UserResponse

class MessageResponse(MessageBase):
    id: UUID4
    chat_id: UUID4
    sender_id: UUID4
    created_at: datetime
    updated_at: datetime
    is_branch_root: bool
    sender: UserResponse
    thread_messages: List['MessageResponse'] = []

    class Config:
        from_attributes = True

class ChatResponse(ChatBase):
    id: UUID4
    created_by: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    messages: List[MessageResponse] = []
    participants: List[UserResponse] = []

    class Config:
        from_attributes = True 