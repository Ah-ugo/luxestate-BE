from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime


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
