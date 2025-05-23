import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

from app.main import app
from app.core.config import settings

# Create test client
client = TestClient(app)

# Mock test data
TEST_USER_ID = uuid.uuid4()
TEST_USER = {
    "id": TEST_USER_ID,
    "email": "test@example.com",
    "username": "testuser",
    "is_active": True,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

TEST_CHAT_ID = uuid.uuid4()
TEST_CHAT = {
    "id": TEST_CHAT_ID,
    "name": "Test Chat",
    "type": "group",
    "is_active": True,
    "created_by": TEST_USER_ID,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "deleted_at": None,
    "participants": [TEST_USER]
}

TEST_MESSAGE_ID = uuid.uuid4()
TEST_MESSAGE = {
    "id": TEST_MESSAGE_ID,
    "chat_id": TEST_CHAT_ID,
    "sender_id": TEST_USER_ID,
    "content": "Hello, World!",
    "message_type": "text",
    "parent_message_id": None,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat(),
    "deleted_at": None
}

# Mock authentication token
TEST_TOKEN = "test_token"

@pytest.fixture
def mock_get_current_user():
    with patch("app.api.deps.get_current_user") as mock:
        mock.return_value = TEST_USER
        yield mock

@pytest.fixture
def mock_db():
    with patch("app.api.deps.get_db") as mock:
        mock.return_value = Mock()
        yield mock

def test_create_chat(client, mock_get_current_user, mock_db, auth_headers):
    """Test creating a new chat"""
    chat_data = {
        "name": "New Chat",
        "type": "group",
        "participant_ids": [str(uuid.uuid4())]
    }
    
    # Mock the create operation
    mock_db.return_value.query().filter().first.return_value = TEST_CHAT
    
    response = client.post(
        f"{settings.API_V1_STR}/chats/",
        headers=auth_headers,
        json=chat_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == TEST_CHAT["name"]
    assert data["type"] == TEST_CHAT["type"]

def test_get_chat(client, mock_get_current_user, mock_db, auth_headers):
    """Test getting a chat by ID"""
    # Mock the database query
    mock_db.return_value.query().filter().first.return_value = TEST_CHAT
    
    response = client.get(
        f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(TEST_CHAT["id"])
    assert data["name"] == TEST_CHAT["name"]

def test_get_chat_not_found(client, mock_get_current_user, mock_db, auth_headers):
    """Test getting non-existent chat"""
    # Mock the database query to return None
    mock_db.return_value.query().filter().first.return_value = None
    
    response = client.get(
        f"{settings.API_V1_STR}/chats/{uuid.uuid4()}",
        headers=auth_headers
    )
    
    assert response.status_code == 404

def test_create_message(client, mock_get_current_user, mock_db, auth_headers):
    """Test creating a new message"""
    message_data = {
        "content": "New message",
        "message_type": "text",
        "parent_message_id": None
    }
    
    # Mock the message service
    with patch("app.services.mongodb.message_service.message_service.create_message") as mock_create:
        mock_create.return_value = TEST_MESSAGE
        
        response = client.post(
            f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}/messages",
            headers=auth_headers,
            json=message_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == TEST_MESSAGE["content"]
        assert data["message_type"] == TEST_MESSAGE["message_type"]

def test_get_chat_messages(client, mock_get_current_user, mock_db, auth_headers):
    """Test getting chat messages"""
    # Mock the message service
    with patch("app.services.mongodb.message_service.message_service.get_chat_messages") as mock_get:
        mock_get.return_value = [TEST_MESSAGE]
        
        response = client.get(
            f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}/messages",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["content"] == TEST_MESSAGE["content"]

def test_get_message_thread(client, mock_get_current_user, mock_db, auth_headers):
    """Test getting message thread"""
    # Mock the message service
    with patch("app.services.mongodb.message_service.message_service.get_message_thread") as mock_get:
        mock_get.return_value = [TEST_MESSAGE]
        
        response = client.get(
            f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}/messages/{TEST_MESSAGE_ID}/thread",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(TEST_MESSAGE["id"])

def test_unauthorized_chat_access(client):
    """Test accessing chat endpoints without authentication"""
    endpoints = [
        f"{settings.API_V1_STR}/chats/",
        f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}",
        f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}/messages"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

def test_delete_chat(client, mock_get_current_user, mock_db, auth_headers):
    """Test deleting a chat"""
    # Mock the delete operation
    mock_db.return_value.query().filter().first.return_value = TEST_CHAT
    
    response = client.delete(
        f"{settings.API_V1_STR}/chats/{TEST_CHAT_ID}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(TEST_CHAT["id"]) 