from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.security import get_current_active_user, get_password_hash, verify_password
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()

class UserOut(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_superuser: bool

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user."""
    return current_user

@router.put("/me", response_model=UserOut)
async def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_active_user)):
    """Update current user's details."""
    update_data = user_update.dict(exclude_unset=True)
    if update_data:
        await current_user.update({"$set": update_data})
    # Beanie's update doesn't return the doc, so we fetch it again
    updated_user = await User.get(current_user.id)
    return updated_user