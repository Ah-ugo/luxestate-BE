import cloudinary
import cloudinary.uploader
import base64
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_image(file_bytes: bytes, folder: str = "listings", public_id: str = None) -> dict:
    """Upload image to Cloudinary"""
    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=f"luxestate/{folder}",
            public_id=public_id,
            transformation=[
                {"quality": "auto:best"},
                {"fetch_format": "auto"},
            ],
        )
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        logger.error(f"Cloudinary upload error: {e}")
        raise


async def upload_pdf(pdf_bytes: bytes, public_id: str) -> str:
    """Upload PDF to Cloudinary and return URL"""
    try:
        result = cloudinary.uploader.upload(
            pdf_bytes,
            folder="luxestate/tour-forms",
            public_id=public_id,
            resource_type="raw",
            format="pdf",
        )
        return result["secure_url"]
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        raise


async def delete_image(public_id: str) -> bool:
    """Delete image from Cloudinary"""
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete error: {e}")
        return False
