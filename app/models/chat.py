from beanie import Document
from pydantic import Field
from datetime import datetime

class ChatMessage(Document):
    sender_email: str
    recipient_email: str # Can be a user's email or a generic "admin_inbox"
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_messages"