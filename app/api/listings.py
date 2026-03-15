from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends, Form
from typing import Optional, List
from app.models.listing import Listing, ListingType, ListingStatus
from app.services.cloudinary_service import upload_image, delete_image
from app.services.listing_service import (
    get_listings, get_listing_by_slug, create_listing, 
    update_listing, seed_listings
)
from app.core.security import get_current_active_superuser
from app.models.user import User
from pydantic import BaseModel
import logging
import json
import re
import secrets

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


@router.get("/slug/{slug}")
async def get_listing_by_slug_endpoint(slug: str):
    """Get single listing by slug"""
    listing = await get_listing_by_slug(slug)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    # Increment views
    listing.views += 1
    await listing.save()
    return listing.dict()


@router.get("/{listing_id}", response_model=Listing)
async def get_listing_by_id(listing_id: str):
    """Get a single listing by its ID."""
    listing = await Listing.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/seed")
async def seed_data():
    """Seed sample listings (dev only)"""
    count = await seed_listings()
    return {"message": f"Seeded {count} listings"}


@router.post("/", status_code=201, response_model=Listing)
async def add_listing(
    # Listing fields from form
    title: str = Form(...),
    description: str = Form(...),
    listing_type: ListingType = Form(...),
    status: ListingStatus = Form(ListingStatus.AVAILABLE),
    price_amount: float = Form(...),
    price_currency: str = Form("USD"),
    price_period: Optional[str] = Form(None),
    bedrooms: int = Form(...),
    bathrooms: float = Form(...),
    size_sqm: float = Form(...),
    location_address: str = Form(...),
    location_city: str = Form(...),
    location_state: str = Form(...),
    location_neighborhood: str = Form(...),
    is_featured: bool = Form(False),
    tags: List[str] = Form([]),
    features: List[str] = Form([]),
    amenities: str = Form('[]', description='JSON string of amenities array, e.g., [{"name": "Pool", "icon": "droplet"}]'),
    # Optional fields
    toilets: Optional[int] = Form(None),
    floor: Optional[int] = Form(None),
    total_floors: Optional[int] = Form(None),
    year_built: Optional[int] = Form(None),
    parking_spaces: Optional[int] = Form(None),
    agent_name: Optional[str] = Form(None),
    agent_phone: Optional[str] = Form(None),
    # Files
    files: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_superuser)
):
    """Admin: Create a new listing using form data."""
    try:
        amenities_list = json.loads(amenities)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for amenities")

    # Generate slug from title
    slug_base = title.lower().strip()
    slug_base = re.sub(r'[^\w\s-]', '', slug_base)
    slug_base = re.sub(r'[\s_-]+', '-', slug_base)
    slug = f"{slug_base}-{secrets.token_hex(2)}"

    listing_dict = {
        "title": title,
        "description": description,
        "listing_type": listing_type,
        "status": status,
        "price": {"amount": price_amount, "currency": price_currency, "period": price_period},
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "size_sqm": size_sqm,
        "location": {
            "address": location_address,
            "city": location_city,
            "state": location_state,
            "neighborhood": location_neighborhood,
        },
        "is_featured": is_featured,
        "tags": tags,
        "features": features,
        "amenities": amenities_list,
        "toilets": toilets if toilets is not None else int(bathrooms),
        "floor": floor, "total_floors": total_floors,
        "year_built": year_built, "parking_spaces": parking_spaces if parking_spaces is not None else 0,
        "agent_name": agent_name, "agent_phone": agent_phone,
        "slug": slug,
    }
    return await create_listing(listing_dict, files)


@router.put("/{listing_id}", response_model=Listing)
async def edit_listing(
    listing_id: str,
    listing_data: Listing,
    current_user: User = Depends(get_current_active_superuser)
):
    """Admin: Update an existing listing."""
    return await update_listing(listing_id, listing_data)


@router.delete("/{listing_id}", status_code=204)
async def remove_listing(listing_id: str, current_user: User = Depends(get_current_active_superuser)):
    """Admin: Delete a listing."""
    listing = await Listing.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    await listing.delete()
    return None


@router.post("/{listing_id}/images", response_model=Listing)
async def add_listing_images(
    listing_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_superuser)
):
    """Admin: Add images to an existing listing."""
    listing = await Listing.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if not listing.images:
        listing.images = []

    for file in files:
        contents = await file.read()
        upload_result = await upload_image(contents, folder="listings")
        image_item = {"url": upload_result["url"], "public_id": upload_result["public_id"], "alt": file.filename}
        listing.images.append(image_item)
    
    await listing.save()
    return listing


@router.delete("/{listing_id}/images/{image_public_id:path}", response_model=Listing)
async def delete_listing_image(
    listing_id: str,
    image_public_id: str,
    current_user: User = Depends(get_current_active_superuser)
):
    """Admin: Delete an image from a listing."""
    listing = await Listing.get(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    await delete_image(image_public_id)
    listing.images = [img for img in listing.images if img.public_id != image_public_id]
    await listing.save()
    return listing
