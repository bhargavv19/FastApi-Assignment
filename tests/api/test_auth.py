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
TEST_USER = {
    "id": str(uuid.uuid4()),
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword123",
    "is_active": True,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

TEST_TOKEN = {
    "access_token": "test_token",
    "token_type": "bearer"
}

@pytest.fixture
def mock_db():
    with patch("app.api.deps.get_db") as mock:
        mock.return_value = Mock()
        yield mock

def test_login_success(client):
    """Test successful login"""
    login_data = {
        "username": TEST_USER["email"],
        "password": TEST_USER["password"],
        "grant_type": "password"
    }
    
    # Mock the authentication
    with patch("app.crud.user.authenticate") as mock_auth:
        mock_auth.return_value = TEST_USER
        
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data=login_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    login_data = {
        "username": "wrong@email.com",
        "password": "wrongpassword",
        "grant_type": "password"
    }
    
    # Mock the authentication to return None
    with patch("app.crud.user.authenticate") as mock_auth:
        mock_auth.return_value = None
        
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data=login_data
        )
        
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

def test_register_success(client):
    """Test successful user registration"""
    register_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpassword123"
    }
    
    # Mock the user creation
    with patch("app.crud.user.create") as mock_create:
        mock_create.return_value = {**TEST_USER, **register_data}
        
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=register_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == register_data["email"]
        assert data["username"] == register_data["username"]
        assert "password" not in data

def test_register_existing_email(client):
    """Test registration with existing email"""
    register_data = {
        "email": TEST_USER["email"],
        "username": "newuser",
        "password": "newpassword123"
    }
    
    # Mock get_by_email to return existing user
    with patch("app.crud.user.get_by_email") as mock_get:
        mock_get.return_value = TEST_USER
        
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=register_data
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

def test_register_existing_username(client):
    """Test registration with existing username"""
    register_data = {
        "email": "new@example.com",
        "username": TEST_USER["username"],
        "password": "newpassword123"
    }
    
    # Mock get_by_email to return None and get_by_username to return existing user
    with patch("app.crud.user.get_by_email") as mock_get_email:
        with patch("app.crud.user.get_by_username") as mock_get_username:
            mock_get_email.return_value = None
            mock_get_username.return_value = TEST_USER
            
            response = client.post(
                f"{settings.API_V1_STR}/auth/register",
                json=register_data
            )
            
            assert response.status_code == 400
            assert "username is already taken" in response.json()["detail"]

def test_register_invalid_data(client):
    """Test registration with invalid data"""
    invalid_data_cases = [
        # Missing email
        {
            "username": "testuser",
            "password": "password123"
        },
        # Invalid email format
        {
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123"
        },
        # Password too short
        {
            "email": "test@example.com",
            "username": "testuser",
            "password": "short"
        }
    ]
    
    for invalid_data in invalid_data_cases:
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json=invalid_data
        )
        assert response.status_code == 422  # Validation error 