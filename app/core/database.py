from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.models.listing import Listing
from app.models.contact import ContactMessage
from app.models.user import User
from app.models.chat import ChatMessage

async def connect_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Initialize Beanie with all document models
    await init_beanie(
        database=client[settings.DATABASE_NAME],
        document_models=[Listing, ContactMessage, User, ChatMessage],
    )

async def close_db():
    pass