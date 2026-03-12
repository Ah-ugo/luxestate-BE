from fastapi import APIRouter, Request, HTTPException
from app.services.payment_service import verify_payment
import hashlib
import hmac
import json
import logging
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def paystack_webhook(request: Request):
    """Handle Paystack webhooks"""
    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    # Verify webhook signature
    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    if computed != signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = json.loads(body)
    event = payload.get("event")

    if event == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")
        logger.info(f"Payment success webhook: {reference}")
        # Additional processing if needed

    return {"status": "ok"}
