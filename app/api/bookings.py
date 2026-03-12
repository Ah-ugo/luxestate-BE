from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.booking import Booking, BookingStatus, TourSlot
from app.services.payment_service import initialize_payment, verify_payment
from app.services.email_service import send_booking_confirmation
from app.services.pdf_service import generate_tour_form_pdf
from app.services.cloudinary_service import upload_pdf
from datetime import datetime
import secrets
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class BookingCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    listing_id: str
    listing_title: str
    listing_slug: str
    listing_address: str
    tour_date: str
    tour_time: str
    message: Optional[str] = None
    num_guests: int = 1


class PaymentInit(BaseModel):
    booking_id: str
    email: str
    amount: int  # in kobo


@router.post("/")
async def create_booking(data: BookingCreate):
    """Create a new tour booking"""
    booking = Booking(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        listing_id=data.listing_id,
        listing_title=data.listing_title,
        listing_slug=data.listing_slug,
        listing_address=data.listing_address,
        tour_slot=TourSlot(date=data.tour_date, time=data.tour_time),
        message=data.message,
        num_guests=data.num_guests,
        booking_ref=f"LUX-{secrets.token_hex(4).upper()}",
    )
    await booking.insert()
    return {
        "booking_id": str(booking.id),
        "booking_ref": booking.booking_ref,
        "status": booking.status,
    }


@router.post("/initialize-payment")
async def init_payment(data: PaymentInit):
    """Initialize Paystack payment for tour booking"""
    booking = await Booking.get(data.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=400, detail="Booking already paid")

    payment_data = await initialize_payment(
        email=data.email,
        amount=data.amount,
        reference=booking.booking_ref,
        metadata={
            "booking_id": str(booking.id),
            "listing_title": booking.listing_title,
            "tour_date": booking.tour_slot.date,
            "tour_time": booking.tour_slot.time,
        }
    )
    return payment_data


@router.get("/verify/{reference}")
async def verify_booking_payment(reference: str):
    """Verify payment and finalize booking"""
    verification = await verify_payment(reference)
    
    if verification.get("status") != "success":
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Find booking by reference
    booking = await Booking.find_one(Booking.booking_ref == reference)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == BookingStatus.PAID:
        return {"message": "Already processed", "booking_ref": booking.booking_ref}

    # Update booking status
    booking.status = BookingStatus.PAID
    booking.payment_reference = reference
    booking.amount_paid = verification.get("amount", 0) / 100
    booking.updated_at = datetime.utcnow()
    await booking.save()

    # Generate PDF form
    try:
        pdf_bytes = generate_tour_form_pdf(booking)
        pdf_url = await upload_pdf(pdf_bytes, f"tour-forms/{booking.booking_ref}")
        booking.form_pdf_url = pdf_url
        await booking.save()

        # Send confirmation email with PDF
        await send_booking_confirmation(booking, pdf_url)
        booking.form_pdf_sent = True
        booking.form_sent_at = datetime.utcnow()
        await booking.save()
    except Exception as e:
        logger.error(f"Error generating/sending PDF: {e}")

    return {
        "success": True,
        "booking_ref": booking.booking_ref,
        "status": booking.status,
        "form_url": booking.form_pdf_url,
        "message": "Payment confirmed! Check your email for the tour form."
    }


@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details"""
    booking = await Booking.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.dict()


@router.get("/ref/{booking_ref}")
async def get_booking_by_ref(booking_ref: str):
    """Get booking by reference"""
    booking = await Booking.find_one(Booking.booking_ref == booking_ref)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking.dict()
