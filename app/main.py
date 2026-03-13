from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import connect_db, close_db
from app.api import listings, auth, contact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    logger.info("✅ Database connected")
    yield
    await close_db()
    logger.info("❌ Database disconnected")


app = FastAPI(
    title="LuxEstate API",
    description="Premium Real Estate Investment Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router, prefix="/api/listings", tags=["Listings"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(contact.router, prefix="/api/contact", tags=["Contact"])


@app.get("/")
async def root():
    return {
        "message": "LuxEstate API v1.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
