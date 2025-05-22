import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.chat import Chat, chat_participants
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import ChatCreate, MessageCreate

def create_test_user(db: Session, email: str, username: str) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password="dummy_hash",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_test_chat(db: Session, creator: User, participants: list[User]) -> Chat:
    chat = Chat(
        name="Test Chat",
        type="group",
        created_by=creator.id,
        is_active=True
    )
    db.add(chat)
    db.flush()
    
    # Add participants
    for participant in participants:
        role = "admin" if participant.id == creator.id else "member"
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

def create_test_message(
    db: Session,
    chat: Chat,
    sender: User,
    content: str,
    parent_message: Message = None
) -> Message:
    message = Message(
        content=content,
        message_type="text",
        chat_id=chat.id,
        sender_id=sender.id,
        parent_message_id=parent_message.id if parent_message else None
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

@pytest.fixture
def test_data(db: Session):
    # Create test users
    user1 = create_test_user(db, "user1@test.com", "user1")
    user2 = create_test_user(db, "user2@test.com", "user2")
    
    # Create test chat
    chat = create_test_chat(db, user1, [user1, user2])
    
    # Create test messages
    root_message = create_test_message(db, chat, user1, "Root message")
    reply1 = create_test_message(db, chat, user2, "Reply 1", root_message)
    reply2 = create_test_message(db, chat, user1, "Reply 2", root_message)
    reply_to_reply = create_test_message(db, chat, user2, "Reply to Reply 1", reply1)
    
    return {
        "user1": user1,
        "user2": user2,
        "chat": chat,
        "root_message": root_message,
        "reply1": reply1,
        "reply2": reply2,
        "reply_to_reply": reply_to_reply
    }

def test_get_chat_branches(client, test_data, db: Session):
    """Test getting all root messages in a chat."""
    response = client.get(f"/api/v1/chats/{test_data['chat'].id}/branches")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # Only one root message
    assert data[0]["content"] == "Root message"

def test_get_message_branch(client, test_data, db: Session):
    """Test getting a message and its direct replies."""
    response = client.get(
        f"/api/v1/chats/{test_data['chat'].id}/messages/{test_data['root_message'].id}/branch"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Root message + 2 direct replies
    assert data[0]["content"] == "Root message"
    assert any(msg["content"] == "Reply 1" for msg in data)
    assert any(msg["content"] == "Reply 2" for msg in data)

def test_get_message_thread(client, test_data, db: Session):
    """Test getting a message and its entire thread."""
    response = client.get(
        f"/api/v1/chats/{test_data['chat'].id}/messages/{test_data['root_message'].id}/thread"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4  # Root message + all replies including nested
    assert data[0]["content"] == "Root message"
    assert any(msg["content"] == "Reply 1" for msg in data)
    assert any(msg["content"] == "Reply 2" for msg in data)
    assert any(msg["content"] == "Reply to Reply 1" for msg in data)

def test_get_nonexistent_message(client, test_data, db: Session):
    """Test getting a non-existent message."""
    response = client.get(
        f"/api/v1/chats/{test_data['chat'].id}/messages/{uuid4()}/branch"
    )
    assert response.status_code == 404

def test_get_message_not_in_chat(client, test_data, db: Session):
    """Test getting a message from a different chat."""
    other_chat = create_test_chat(db, test_data["user1"], [test_data["user1"]])
    other_message = create_test_message(db, other_chat, test_data["user1"], "Other message")
    
    response = client.get(
        f"/api/v1/chats/{test_data['chat'].id}/messages/{other_message.id}/branch"
    )
    assert response.status_code == 404 