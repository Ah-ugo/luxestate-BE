from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional, List
from app.models.listing import Listing, ListingType, ListingStatus
from app.services.cloudinary_service import upload_image
from app.services.listing_service import (
    get_listings, get_listing_by_slug, create_listing, 
    update_listing, seed_listings
)
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ListingFilter(BaseModel):
    listing_type: Optional[str] = None
    city: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    is_featured: Optional[bool] = None
    search: Optional[str] = None


@router.get("/")
async def list_listings(
    listing_type: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    bedrooms: Optional[int] = Query(None),
    is_featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    sort_by: str = Query("created_at"),
    sort_order: int = Query(-1),
):
    """Get all listings with filtering and pagination"""
    filters = {
        "listing_type": listing_type,
        "city": city,
        "min_price": min_price,
        "max_price": max_price,
        "bedrooms": bedrooms,
        "is_featured": is_featured,
        "search": search,
    }
    result = await get_listings(filters, page, limit, sort_by, sort_order)
    return result


@router.get("/featured")
async def featured_listings():
    """Get featured listings for homepage"""
    listings = await Listing.find(
        Listing.is_featured == True,
        Listing.status == ListingStatus.AVAILABLE
    ).limit(6).to_list()
    return [l.dict() for l in listings]


@router.get("/cities")
async def get_cities():
    """Get unique cities"""
    pipeline = [
        {"$group": {"_id": "$location.city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    result = await Listing.aggregate(pipeline).to_list()
    return [{"city": r["_id"], "count": r["count"]} for r in result if r["_id"]]


@router.get("/stats")
async def get_stats():
    """Get platform statistics"""
    total = await Listing.count()
    for_rent = await Listing.find(Listing.listing_type == ListingType.RENT).count()
    for_sale = await Listing.find(Listing.listing_type == ListingType.BUY).count()
    available = await Listing.find(Listing.status == ListingStatus.AVAILABLE).count()
    return {
        "total_listings": total,
        "for_rent": for_rent,
        "for_sale": for_sale,
        "available": available,
        "satisfied_clients": 2847,
        "years_experience": 12,
        "cities": 8,
    }


@router.get("/{slug}")
async def get_listing(slug: str):
    """Get single listing by slug"""
    listing = await Listing.find_one(Listing.slug == slug)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    # Increment views
    listing.views += 1
    await listing.save()
    return listing.dict()


@router.post("/seed")
async def seed_data():
    """Seed sample listings (dev only)"""
    count = await seed_listings()
    return {"message": f"Seeded {count} listings"}
