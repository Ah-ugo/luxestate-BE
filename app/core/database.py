from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.listing import Listing
from app.models.booking import Booking
from app.models.user import User
from app.models.contact import ContactMessage
import logging

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    await init_beanie(
        database=db,
        document_models=[Listing, Booking, User, ContactMessage]
    )
    logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_db():
    global client
    if client:
        client.close()


def get_db():
    return client[settings.DATABASE_NAME]
