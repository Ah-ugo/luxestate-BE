from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "LuxEstate"
    DEBUG: bool = False

    MONGODB_URL: str
    DATABASE_NAME: str = "luxestate"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    RESEND_API_KEY: str
    FROM_EMAIL: str

    FRONTEND_URL: str = "http://localhost:3000"

    # Optional Paystack keys if needed later
    PAYSTACK_SECRET_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
