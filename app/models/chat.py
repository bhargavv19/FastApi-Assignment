from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.message import Message

# Association table for chat participants
chat_participants = Table(
    "chat_participants",
    Base.metadata,
    Column("chat_id", PGUUID(as_uuid=True), ForeignKey("chats.id"), primary_key=True),
    Column("user_id", PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role", String(50), nullable=False),  # admin, member
    Column("created_at", DateTime, default=datetime.utcnow),
)

class Chat(Base):
    __tablename__ = "chats"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # direct, group, etc.
    is_active = Column(Boolean(), default=True)
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    participants = relationship(
        "User",
        secondary=chat_participants,
        back_populates="chat_participations"
    ) 