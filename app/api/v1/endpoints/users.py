from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate,
    current_user = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user.
    """
    user = crud.user.update(db=db, db_obj=current_user, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: str,
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = crud.user.get(db=db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for username or email"),
    current_user = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve users with optional search and pagination.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Number of records to return (max 100)
    - **search**: Optional search term to filter users by username or email
    """
    query = db.query(models.User)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.User.username.ilike(search_term),
                models.User.email.ilike(search_term)
            )
        )
    
    users = query.offset(skip).limit(limit).all()
    return users 