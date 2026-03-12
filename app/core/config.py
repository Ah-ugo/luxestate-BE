from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "LuxEstate"
    DEBUG: bool = False
    SECRET_KEY: str = "luxestate-super-secret-key-change-in-prod"

    # MongoDB Atlas
    MONGODB_URL: str = "mongodb+srv://user:password@cluster.mongodb.net"
    DATABASE_NAME: str = "luxestate"

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "luxestate"

    # Payment Gateway Keys
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""

    # Email via SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@luxestate.com"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"

    # Tour booking fee in kobo (Paystack uses kobo, 100 naira = 10000 kobo)
    # $100 USD = 10000 cents (using cents/kobo logic for amount)
    TOUR_FEE_KOBO: int = 10000  # 10000 units = 100.00

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
