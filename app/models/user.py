from beanie import Document
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime


class User(Document):
    email: str
    full_name: str
    phone: Optional[str] = None
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    avatar_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


class ContactMessage(Document):
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
    listing_id: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "contact_messages"
