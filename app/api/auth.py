from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.models.user import User
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.services.email_service import send_password_reset_email
from datetime import timedelta, datetime
import logging
from jose import jwt

router = APIRouter()
logger = logging.getLogger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Handles user login and returns a JWT access token."""
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( # In a real app, you might add roles to the token
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest):
    """Register a new user"""
    user_exists = await User.find_one(User.email == req.email)
    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    user = User(
        email=req.email,
        hashed_password=get_password_hash(req.password),
        first_name=req.first_name,
        last_name=req.last_name
    )
    await user.insert()
    return {"message": "Registration successful"}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    """
    Handles a forgot password request. Finds the user, generates a reset token,
    and sends a password reset email.
    """
    user = await User.find_one(User.email == req.email)
    if not user:
        # Note: We don't want to reveal if an email exists in the system
        logger.warning(f"Password reset attempt for non-existent user: {req.email}")
        return {"message": "If an account with that email exists, a reset link has been sent."}

    # Create a short-lived token for password reset
    expires = datetime.utcnow() + timedelta(hours=1)
    token_payload = {"sub": user.email, "exp": expires, "scope": "reset_password"}
    token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"

    try:
        await send_password_reset_email(to=user.email, reset_link=reset_link)
        return {"message": "If an account with that email exists, a reset link has been sent."}
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        raise HTTPException(status_code=500, detail="Could not send reset email.")


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """
    Resets the user's password using a valid token.
    """
    try:
        payload = jwt.decode(
            req.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("scope") != "reset_password":
            raise HTTPException(status_code=401, detail="Invalid token scope")

        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Password reset token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid password reset token")

    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Hash the new password and update the user
    hashed_password = get_password_hash(req.password)
    user.hashed_password = hashed_password
    user.updated_at = datetime.utcnow()
    await user.save()

    return {"message": "Password has been reset successfully."}


@router.post("/seed-admin", status_code=status.HTTP_201_CREATED)
async def seed_admin_user():
    """Create a default admin user if one doesn't exist."""
    admin_email = "admin@luxestate.us"
    user_exists = await User.find_one(User.email == admin_email)
    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="Admin user with this email already exists"
        )
    
    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash("AdminPassword123!"),
        first_name="Admin",
        last_name="User",
        is_superuser=True
    )
    await admin_user.insert()
    return {"message": f"Admin user '{admin_email}' created successfully."}