from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter()


class ContactCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
    listing_id: Optional[str] = None


@router.post("/")
async def send_contact(data: ContactCreate):
    """Submit contact message"""
    from app.models.contact import ContactMessage
    from app.services.email_service import send_contact_notification

    msg = ContactMessage(
        name=data.name,
        email=data.email,
        phone=data.phone,
        subject=data.subject,
        message=data.message,
        listing_id=data.listing_id,
    )
    await msg.insert()

    try:
        await send_contact_notification(msg)
    except Exception as e:
        pass  # Don't fail on email error

    return {"message": "Message sent successfully", "id": str(msg.id)}
