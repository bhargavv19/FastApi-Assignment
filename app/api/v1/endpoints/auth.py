from datetime import timedelta
from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Form, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.crud.user import get_by_email, get_by_username, authenticate, create

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/login", response_model=schemas.Token)
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        logger.info(f"Login attempt for username: {form_data.username}")
        
        # Validate grant type
        if not form_data.grant_type or form_data.grant_type != "password":
            logger.warning(f"Invalid grant type: {form_data.grant_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid grant type. Use 'password' for username/password authentication."
            )
        
        # Validate username and password
        if not form_data.username or not form_data.password:
            logger.warning("Missing username or password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required."
            )
        
        # Authenticate user
        user = authenticate(
            db, email=form_data.username, password=form_data.password
        )
        if not user:
            logger.warning(f"Authentication failed for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif not user.is_active:
            logger.warning(f"Inactive user attempted login: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
            
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        logger.info(f"Login successful for user: {form_data.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

@router.post("/register", response_model=schemas.User)
async def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate = Body(
        ...,
        example={
            "email": "user@example.com",
            "username": "username",
            "password": "password123"
        }
    )
) -> Any:
    """
    Create new user.
    """
    try:
        logger.info(f"Registration attempt with data: {user_in.dict(exclude={'password'})}")
        
        # Check if user exists
        user = get_by_email(db, email=user_in.email)
        if user:
            logger.warning(f"Registration failed: Email {user_in.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system."
            )
        
        # Check if username exists
        user = get_by_username(db, username=user_in.username)
        if user:
                logger.warning(f"Registration failed: Username {user_in.username} already taken")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The username is already taken."
                )
        
        # Create user
        logger.info(f"Creating new user with username: {user_in.username}")
        user = create(db, obj_in=user_in)
        logger.info(f"User created successfully with ID: {user.id}")
        return user
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )