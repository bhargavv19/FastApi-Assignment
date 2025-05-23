import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

from app.core.config import settings

# Mock test data
TEST_USER_ID = str(uuid.uuid4())
TEST_USER = {
    "id": TEST_USER_ID,
    "email": "test@example.com",
    "username": "testuser",
    "is_active": True,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

TEST_CHAT_ID = str(uuid.uuid4())
TEST_CHAT = {
    "id": TEST_CHAT_ID,
    "user_id": TEST_USER_ID,
    "title": "Test Chat",
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

TEST_MESSAGE_ID = str(uuid.uuid4())
TEST_MESSAGE = {
    "id": TEST_MESSAGE_ID,
    "chat_id": TEST_CHAT_ID,
    "role": "user",
    "content": "Hello, how are you?",
    "created_at": datetime.utcnow().isoformat()
}

def test_create_chat(client):
    """Test creating a new chat"""
    chat_data = {
        "title": "New Chat"
    }
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.create") as mock_create:
            mock_get_user.return_value = TEST_USER
            mock_create.return_value = {**TEST_CHAT, **chat_data}
            
            response = client.post(
                f"{settings.API_V1_STR}/chat/",
                headers={"Authorization": "Bearer test_token"},
                json=chat_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == chat_data["title"]
            assert data["user_id"] == TEST_USER_ID

def test_get_chat(client):
    """Test getting a chat by ID"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get:
            mock_get_user.return_value = TEST_USER
            mock_get.return_value = TEST_CHAT
            
            response = client.get(
                f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == TEST_CHAT_ID
            assert data["title"] == TEST_CHAT["title"]

def test_get_chat_not_found(client):
    """Test getting non-existent chat"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get:
            mock_get_user.return_value = TEST_USER
            mock_get.return_value = None
            
            response = client.get(
                f"{settings.API_V1_STR}/chat/{uuid.uuid4()}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            assert response.json()["detail"] == "Chat not found"

def test_get_user_chats(client):
    """Test getting all chats for a user"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get_multi_by_user") as mock_get_multi:
            mock_get_user.return_value = TEST_USER
            mock_get_multi.return_value = [TEST_CHAT]
            
            response = client.get(
                f"{settings.API_V1_STR}/chat/",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == TEST_CHAT_ID

def test_update_chat(client):
    """Test updating a chat"""
    update_data = {
        "title": "Updated Chat Title"
    }
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get:
            with patch("app.crud.chat.update") as mock_update:
                mock_get_user.return_value = TEST_USER
                mock_get.return_value = TEST_CHAT
                mock_update.return_value = {**TEST_CHAT, **update_data}
                
                response = client.put(
                    f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}",
                    headers={"Authorization": "Bearer test_token"},
                    json=update_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["title"] == update_data["title"]

def test_delete_chat(client):
    """Test deleting a chat"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get:
            with patch("app.crud.chat.remove") as mock_remove:
                mock_get_user.return_value = TEST_USER
                mock_get.return_value = TEST_CHAT
                mock_remove.return_value = TEST_CHAT
                
                response = client.delete(
                    f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == TEST_CHAT_ID

def test_create_message(client):
    """Test creating a new message"""
    message_data = {
        "role": "user",
        "content": "Hello, how are you?"
    }
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get_chat:
            with patch("app.crud.message.create") as mock_create:
                mock_get_user.return_value = TEST_USER
                mock_get_chat.return_value = TEST_CHAT
                mock_create.return_value = {**TEST_MESSAGE, **message_data}
                
                response = client.post(
                    f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}/messages",
                    headers={"Authorization": "Bearer test_token"},
                    json=message_data
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["content"] == message_data["content"]
                assert data["role"] == message_data["role"]

def test_get_chat_messages(client):
    """Test getting all messages in a chat"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.chat.get") as mock_get_chat:
            with patch("app.crud.message.get_multi_by_chat") as mock_get_messages:
                mock_get_user.return_value = TEST_USER
                mock_get_chat.return_value = TEST_CHAT
                mock_get_messages.return_value = [TEST_MESSAGE]
                
                response = client.get(
                    f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}/messages",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 1
                assert data[0]["id"] == TEST_MESSAGE_ID

def test_unauthorized_access(client):
    """Test accessing endpoints without authentication"""
    endpoints = [
        f"{settings.API_V1_STR}/chat/",
        f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}",
        f"{settings.API_V1_STR}/chat/{TEST_CHAT_ID}/messages"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden 