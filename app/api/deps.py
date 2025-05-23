from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
import logging

from app.db.session import SessionLocal
from app.core.config import settings
from app.schemas.token import TokenPayload
from app.crud.user import get
from app import crud, models, schemas
from app.core import security

# Configure logging
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> dict:
    try:
        logger.info("Validating access token")
        logger.debug(f"Token received: {token[:10]}...")  # Log first 10 chars of token
        
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.debug(f"Token payload: {payload}")
        
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            logger.error("Token subject is None")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication token",
            )
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # Fetch user from database
    user = get(db, id=token_data.sub)
    if not user:
        logger.error(f"User not found for token sub: {token_data.sub}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    logger.info(f"User authenticated: {user.email}")
    return user 

async def get_current_user_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db)
) -> models.User:
    try:
        # Extract token from query parameters
        query_params = dict(websocket.query_params)
        token = query_params.get("token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication token",
            )
            
    except (jwt.JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = crud.user["get"](db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
        
    logger.info(f"User authenticated: {user.email}")
    return user 