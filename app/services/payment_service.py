import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

PAYSTACK_BASE = "https://api.paystack.co"


async def initialize_payment(
    email: str,
    amount: int,  # in kobo
    reference: str,
    metadata: dict = None,
    callback_url: str = None,
) -> dict:
    """Initialize a Paystack payment"""
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "amount": amount,
        "reference": reference,
        "callback_url": callback_url or f"{settings.FRONTEND_URL}/booking/verify",
        "metadata": metadata or {},
        "channels": ["card", "bank", "ussd", "qr", "mobile_money", "bank_transfer"],
        "currency": "NGN",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYSTACK_BASE}/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        data = response.json()

    if not data.get("status"):
        logger.error(f"Paystack init error: {data}")
        raise Exception(f"Payment initialization failed: {data.get('message')}")

    return {
        "authorization_url": data["data"]["authorization_url"],
        "access_code": data["data"]["access_code"],
        "reference": data["data"]["reference"],
    }


async def verify_payment(reference: str) -> dict:
    """Verify a Paystack payment"""
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYSTACK_BASE}/transaction/verify/{reference}",
            headers=headers,
            timeout=30.0,
        )
        data = response.json()

    if not data.get("status"):
        raise Exception(f"Verification failed: {data.get('message')}")

    transaction = data.get("data", {})
    return {
        "status": transaction.get("status"),
        "amount": transaction.get("amount"),
        "reference": transaction.get("reference"),
        "paid_at": transaction.get("paid_at"),
        "channel": transaction.get("channel"),
        "customer": transaction.get("customer", {}),
    }
