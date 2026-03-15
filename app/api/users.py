from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User
from app.core.security import get_current_active_user, get_password_hash, verify_password
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

router = APIRouter()

class UserOut(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_superuser: bool

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

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

@router.post("/me/change-password")
async def change_password_me(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Change current user's password."""
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    hashed_password = get_password_hash(password_data.new_password)
    current_user.hashed_password = hashed_password
    current_user.updated_at = datetime.utcnow()
    await current_user.save()
    
    return {"message": "Password updated successfully"}