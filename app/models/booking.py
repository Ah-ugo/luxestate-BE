from beanie import Document, Link
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, date
from enum import Enum
from bson import ObjectId


class BookingStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TourSlot(BaseModel):
    date: str  # ISO date string
    time: str  # e.g. "10:00 AM"


class Booking(Document):
    # Guest Info
    first_name: str
    last_name: str
    email: str
    phone: str
    
    # Listing ref
    listing_id: str
    listing_title: str
    listing_slug: str
    listing_address: str
    
    # Tour Details
    tour_slot: TourSlot
    message: Optional[str] = None
    num_guests: int = 1
    
    # Payment
    status: BookingStatus = BookingStatus.PENDING
    payment_reference: Optional[str] = None
    paystack_transaction_id: Optional[str] = None
    amount_paid: float = 0
    currency: str = "NGN"
    
    # Form PDF
    form_pdf_url: Optional[str] = None
    form_pdf_sent: bool = False
    form_sent_at: Optional[datetime] = None
    
    # Booking reference (human readable)
    booking_ref: str = ""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bookings"
