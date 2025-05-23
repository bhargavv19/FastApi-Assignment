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
TEST_USER_ID = str(uuid.uuid4())
TEST_USER = {
    "id": TEST_USER_ID,
    "email": "test@example.com",
    "username": "testuser",
    "is_active": True,
    "created_at": datetime.utcnow().isoformat(),
    "updated_at": datetime.utcnow().isoformat()
}

TEST_USERS = [
    {
        "id": str(uuid.uuid4()),
        "email": f"user{i}@example.com",
        "username": f"user{i}",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    for i in range(1, 4)
]

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

def test_read_user_me(client):
    """Test getting current user information"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        mock_get_user.return_value = TEST_USER
        
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER["email"]
        assert data["username"] == TEST_USER["username"]

def test_update_user_me(client):
    """Test updating current user information"""
    update_data = {
        "username": "newusername",
        "email": "newemail@example.com"
    }
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.update") as mock_update:
            mock_get_user.return_value = TEST_USER
            mock_update.return_value = {**TEST_USER, **update_data}
            
            response = client.put(
                f"{settings.API_V1_STR}/users/me",
                headers={"Authorization": "Bearer test_token"},
                json=update_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == update_data["username"]
            assert data["email"] == update_data["email"]

def test_read_user_by_id(client):
    """Test getting user by ID"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.get") as mock_get:
            mock_get_user.return_value = TEST_USER
            mock_get.return_value = TEST_USER
            
            response = client.get(
                f"{settings.API_V1_STR}/users/{TEST_USER_ID}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == TEST_USER["id"]
            assert data["email"] == TEST_USER["email"]

def test_read_user_by_id_not_found(client):
    """Test getting non-existent user"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.get") as mock_get:
            mock_get_user.return_value = TEST_USER
            mock_get.return_value = None
            
            response = client.get(
                f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            assert response.json()["detail"] == "User not found"

def test_read_users(client):
    """Test getting list of users"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.get_multi") as mock_get_multi:
            mock_get_user.return_value = TEST_USER
            mock_get_multi.return_value = TEST_USERS
            
            response = client.get(
                f"{settings.API_V1_STR}/users/",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(TEST_USERS)
            assert data[0]["email"] == TEST_USERS[0]["email"]

def test_read_users_with_search(client):
    """Test searching users"""
    search_term = "user1"
    filtered_users = [u for u in TEST_USERS if search_term in u["username"]]
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.get_multi") as mock_get_multi:
            mock_get_user.return_value = TEST_USER
            mock_get_multi.return_value = filtered_users
            
            response = client.get(
                f"{settings.API_V1_STR}/users/?search={search_term}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(filtered_users)
            assert search_term in data[0]["username"]

def test_read_users_pagination(client):
    """Test user list pagination"""
    skip = 1
    limit = 2
    paginated_users = TEST_USERS[skip:skip+limit]
    
    with patch("app.api.deps.get_current_user") as mock_get_user:
        with patch("app.crud.user.get_multi") as mock_get_multi:
            mock_get_user.return_value = TEST_USER
            mock_get_multi.return_value = paginated_users
            
            response = client.get(
                f"{settings.API_V1_STR}/users/?skip={skip}&limit={limit}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == len(paginated_users)

def test_unauthorized_access(client):
    """Test accessing endpoints without authentication"""
    endpoints = [
        f"{settings.API_V1_STR}/users/me",
        f"{settings.API_V1_STR}/users/{TEST_USER_ID}",
        f"{settings.API_V1_STR}/users/"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403]  # Unauthorized or Forbidden

def test_invalid_pagination_params(client):
    """Test invalid pagination parameters"""
    with patch("app.api.deps.get_current_user") as mock_get_user:
        mock_get_user.return_value = TEST_USER
        
        invalid_params = [
            {"skip": -1, "limit": 10},
            {"skip": 0, "limit": 101},
            {"skip": "invalid", "limit": 10}
        ]
        
        for params in invalid_params:
            response = client.get(
                f"{settings.API_V1_STR}/users/",
                params=params,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 422  # Unprocessable Entity 