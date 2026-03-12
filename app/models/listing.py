from beanie import Document, Indexed
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ListingType(str, Enum):
    RENT = "rent"
    BUY = "buy"
    BOTH = "both"


class ListingStatus(str, Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RENTED = "rented"
    PENDING = "pending"


class AmenityItem(BaseModel):
    name: str
    icon: str


class ImageItem(BaseModel):
    url: str
    public_id: str
    alt: Optional[str] = ""


class PriceDetail(BaseModel):
    amount: float
    currency: str = "NGN"
    period: Optional[str] = None  # e.g. "per year" for rent


class Location(BaseModel):
    address: str
    city: str
    state: str
    country: str = "Nigeria"
    lat: Optional[float] = None
    lng: Optional[float] = None
    neighborhood: Optional[str] = None


class Listing(Document):
    title: str
    slug: Indexed(str, unique=True)
    description: str
    listing_type: ListingType
    status: ListingStatus = ListingStatus.AVAILABLE
    
    # Pricing
    price: PriceDetail
    service_charge: Optional[PriceDetail] = None
    
    # Property Details
    bedrooms: int
    bathrooms: int
    toilets: int
    size_sqm: float
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    year_built: Optional[int] = None
    parking_spaces: int = 0
    
    # Location
    location: Location
    
    # Media
    images: List[ImageItem] = []
    virtual_tour_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Features
    amenities: List[AmenityItem] = []
    features: List[str] = []
    
    # Metadata
    is_featured: bool = False
    is_new: bool = True
    views: int = 0
    tour_count: int = 0
    tags: List[str] = []
    
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_image: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "listings"
        indexes = [
            "listing_type",
            "status",
            "is_featured",
            [("location.city", 1)],
            [("price.amount", 1)],
            [("created_at", -1)],
        ]
