from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any

import logging
from app.core.security import get_current_active_user, get_current_active_superuser
from app.models.user import User
router = APIRouter()


class ContactCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    message: str
    listing_id: Optional[str] = None
    listing_title: Optional[str] = None


@router.post("/")
async def send_contact(data: ContactCreate):
    """Submit contact message"""
    from app.models.contact import ContactMessage
    from app.services.email_service import send_contact_notification, send_tour_request_acknowledgement

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
        
        # If this is a tour request (has listing_id), send acknowledgement to user
        if data.listing_id:
            booking_details = {
                "name": data.name,
                "email": data.email,
                "listing_title": data.listing_title or "Requested Property"
            }
            await send_tour_request_acknowledgement(booking_details)
    except Exception as e:
        # Don't fail the request if email fails, but log it
        logging.error(f"Failed to send notification emails: {e}")

    return {"message": "Message sent successfully", "id": str(msg.id)}


@router.get("/", response_model=List[Dict[str, Any]])
async def get_all_messages(current_user: User = Depends(get_current_active_superuser)):
    """Get all contact messages (Admin)"""
    from app.models.contact import ContactMessage
    messages = await ContactMessage.find_all().to_list()
    return [m.dict() for m in messages]


@router.get("/my-requests", response_model=List[Dict[str, Any]])
async def get_my_messages(current_user: User = Depends(get_current_active_user)):
    """Get messages for the current user"""
    from app.models.contact import ContactMessage
    messages = await ContactMessage.find(ContactMessage.email == current_user.email).to_list()
    return [m.dict() for m in messages]


@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_superuser)):
    """Get admin dashboard stats"""
    from app.models.contact import ContactMessage
    total_messages = await ContactMessage.find_all().count()
    return {"total_messages": total_messages}
