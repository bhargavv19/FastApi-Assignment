from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
import uuid
import re

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    username: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    username: str = Field(..., min_length=3, max_length=50, description="Username of the user")
    password: str = Field(..., min_length=8, description="Password of the user")

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError('Username must be alphanumeric and can contain underscores and hyphens')
        return v

    @validator('password')
    def password_strength(cls, v):
        if not re.match(r"^(?=.*[A-Za-z])(?=.*[0-9])(?=.*[@$!%*#?&])[A-Za-z0-9@$!%*#?&]{8,}$", v):
            raise ValueError('Password must contain at least one letter, one number, and one special character')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "username123",
                "password": "Password123!"
            }
        }

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)

class UserInDBBase(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str 