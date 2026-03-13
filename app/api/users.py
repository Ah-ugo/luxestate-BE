from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.security import get_current_active_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserOut(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    is_superuser: bool

@router.get("/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user."""
    return current_user