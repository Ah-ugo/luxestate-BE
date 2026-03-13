from app.models.listing import Listing, ListingType, ListingStatus, PriceDetail, Location, ImageItem, AmenityItem
from typing import Optional, Dict, Any
import math
import base64
import logging
from fastapi import UploadFile
from app.services.cloudinary_service import upload_image

logger = logging.getLogger(__name__)



async def get_listings(filters: Dict, page: int = 1, limit: int = 12, sort_by: str = "created_at", sort_order: int = -1):
    """Get listings with filters and pagination"""
    query = {}
    
    if filters.get("listing_type"):
        query["listing_type"] = filters["listing_type"]
    
    if filters.get("city"):
        query["location.city"] = {"$regex": filters["city"], "$options": "i"}
    
    if filters.get("bedrooms") is not None:
        query["bedrooms"] = filters["bedrooms"]

    if filters.get("is_featured") is not None:
        query["is_featured"] = filters["is_featured"]

    price_filter = {}
    if filters.get("min_price"):
        price_filter["$gte"] = filters["min_price"]
    if filters.get("max_price"):
        price_filter["$lte"] = filters["max_price"]
    if price_filter:
        query["price.amount"] = price_filter

    if filters.get("search"):
        query["$or"] = [
            {"title": {"$regex": filters["search"], "$options": "i"}},
            {"description": {"$regex": filters["search"], "$options": "i"}},
            {"location.city": {"$regex": filters["search"], "$options": "i"}},
            {"location.address": {"$regex": filters["search"], "$options": "i"}},
            {"tags": {"$in": [filters["search"].lower()]}},
        ]

    skip = (page - 1) * limit
    total = await Listing.find(query).count()
    sort_field = f"-{sort_by}" if sort_order == -1 else sort_by

    listings = await Listing.find(query).sort(sort_field).skip(skip).limit(limit).to_list()

    return {
        "listings": [l.dict() for l in listings],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit),
        "has_next": page * limit < total,
        "has_prev": page > 1,
    }


async def get_listing_by_slug(slug: str):
    return await Listing.find_one(Listing.slug == slug)


async def create_listing(data: dict, files: list[UploadFile] = []):
    """Create a new listing with image uploads"""
    listing = Listing(**data)

    # Handle image uploads
    if files:
        listing.images = []
        for file in files:
            contents = await file.read()
            upload_result = await upload_image(contents, folder="listings")
            image_item = ImageItem(url=upload_result["url"], public_id=upload_result["public_id"], alt=file.filename)
            listing.images.append(image_item)

    await listing.insert()
    return listing


async def update_listing(listing_id: str, data: dict):
    listing = await Listing.get(listing_id)
    if not listing:
        return None
    for key, value in data.items():
        setattr(listing, key, value)
    await listing.save()
    return listing


SAMPLE_IMAGES = {
    "luxury_apt": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&q=80",
    "modern_living": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&q=80",
    "penthouse": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80",
    "bedroom": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80",
    "kitchen": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=800&q=80",
    "pool": "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800&q=80",
    "terrace": "https://images.unsplash.com/photo-1559508551-44bff1de756b?w=800&q=80",
    "lobby": "https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=800&q=80",
}

SEED_LISTINGS = [
    {
        "title": "The Tribeca Pinnacle — Penthouse Suite",
        "slug": "tribeca-pinnacle-penthouse-suite",
        "description": "Experience the pinnacle of luxury living in this breathtaking penthouse positioned on the 32nd floor of Manhattan's most prestigious tower. Featuring panoramic city views, bespoke Italian finishes, and a private rooftop terrace that redefines urban sophistication.",
        "listing_type": ListingType.BUY,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=12500000, currency="USD"),
        "bedrooms": 5,
        "bathrooms": 6,
        "toilets": 7,
        "size_sqm": 680,
        "floor": 32,
        "total_floors": 35,
        "year_built": 2022,
        "parking_spaces": 4,
        "location": Location(
            address="101 Warren Street",
            city="New York",
            state="NY",
            neighborhood="Tribeca",
            lat=40.7154,
            lng=-74.0110,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["penthouse"], alt="Penthouse exterior", public_id="lux1"),
            ImageItem(url=SAMPLE_IMAGES["modern_living"], alt="Living area", public_id="lux1a"),
            ImageItem(url=SAMPLE_IMAGES["bedroom"], alt="Master bedroom", public_id="lux1b"),
        ],
        "amenities": [
            AmenityItem(name="Private Pool", icon="droplet"),
            AmenityItem(name="Rooftop Terrace", icon="sun"),
            AmenityItem(name="Smart Home", icon="cpu"),
            AmenityItem(name="Private Cinema", icon="film"),
            AmenityItem(name="Wine Cellar", icon="wine"),
            AmenityItem(name="Concierge", icon="briefcase"),
            AmenityItem(name="Gym & Spa", icon="activity"),
            AmenityItem(name="24/7 Security", icon="shield"),
        ],
        "features": ["Italian marble floors", "Chef's kitchen", "Walk-in wardrobes", "Home automation", "Butler's pantry"],
        "is_featured": True,
        "is_new": True,
        "tags": ["luxury", "penthouse", "city view", "tribeca"],
        "agent_name": "Alexander Sterling",
        "agent_phone": "+1 212 555 0123",
    },
    {
        "title": "Harbor View Apartments — 3 Bedroom Luxury",
        "slug": "harbor-view-apartments-3-bedroom",
        "description": "Elevated living in the heart of Miami Beach. These meticulously designed apartments offer sweeping views of the ocean, premium European fittings, and access to world-class amenities. Perfect for the discerning executive.",
        "listing_type": ListingType.RENT,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=18000, currency="USD", period="per month"),
        "service_charge": PriceDetail(amount=500, currency="USD", period="per month"),
        "bedrooms": 3,
        "bathrooms": 4,
        "toilets": 4,
        "size_sqm": 285,
        "floor": 8,
        "total_floors": 20,
        "year_built": 2021,
        "parking_spaces": 2,
        "location": Location(
            address="4500 Collins Ave",
            city="Miami Beach",
            state="FL",
            neighborhood="Mid-Beach",
            lat=25.8179,
            lng=-80.1226,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["luxury_apt"], alt="Harbour View exterior", public_id="lux2"),
            ImageItem(url=SAMPLE_IMAGES["kitchen"], alt="Kitchen", public_id="lux2a"),
            ImageItem(url=SAMPLE_IMAGES["terrace"], alt="Terrace", public_id="lux2b"),
        ],
        "amenities": [
            AmenityItem(name="Swimming Pool", icon="droplet"),
            AmenityItem(name="Gym", icon="activity"),
            AmenityItem(name="24/7 Security", icon="shield"),
            AmenityItem(name="Backup Power", icon="zap"),
            AmenityItem(name="Water Treatment", icon="droplet"),
            AmenityItem(name="Children's Play Area", icon="smile"),
        ],
        "features": ["Creek views", "BQ", "Fitted kitchen", "Central air conditioning", "Video intercom"],
        "is_featured": True,
        "is_new": True,
        "tags": ["rent", "miami", "ocean view", "executive"],
        "agent_name": "Isabella Cortez",
        "agent_phone": "+1 305 555 7890",
    },
    {
        "title": "Hudson Yards — The Signature Tower",
        "slug": "hudson-yards-signature-tower",
        "description": "Live in the sky. Hudson Yards' most coveted address presents The Signature Tower — an architectural marvel rising from the new West Side. Infinity pool, private club access, and residences that set a new standard.",
        "listing_type": ListingType.BOTH,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=8500000, currency="USD"),
        "bedrooms": 4,
        "bathrooms": 5,
        "toilets": 6,
        "size_sqm": 420,
        "floor": 18,
        "total_floors": 40,
        "year_built": 2023,
        "parking_spaces": 3,
        "location": Location(
            address="15 Hudson Yards",
            city="New York",
            state="NY",
            neighborhood="Chelsea",
            lat=40.7538,
            lng=-74.0022,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["pool"], alt="Infinity pool", public_id="lux3"),
            ImageItem(url=SAMPLE_IMAGES["lobby"], alt="Grand lobby", public_id="lux3a"),
            ImageItem(url=SAMPLE_IMAGES["modern_living"], alt="Living room", public_id="lux3b"),
        ],
        "amenities": [
            AmenityItem(name="Infinity Pool", icon="droplet"),
            AmenityItem(name="Marina Access", icon="anchor"),
            AmenityItem(name="Helipad", icon="wind"),
            AmenityItem(name="Spa & Wellness", icon="heart"),
            AmenityItem(name="Business Center", icon="briefcase"),
            AmenityItem(name="Fine Dining", icon="coffee"),
        ],
        "features": ["Atlantic Ocean views", "Smart home system", "Private lift", "Italian kitchen", "Marble bathrooms"],
        "is_featured": True,
        "is_new": False,
        "tags": ["hudson yards", "luxury", "investment"],
        "agent_name": "James Sinclair",
        "agent_phone": "+1 646 555 4321",
    },
    {
        "title": "Santa Monica — Contemporary 2 Bedroom",
        "slug": "santa-monica-contemporary-2bed",
        "description": "Modern urban living in a boutique development. These sleek, thoughtfully designed apartments combine contemporary aesthetics with practical living, situated moments from the finest restaurants and entertainment on the Pier.",
        "listing_type": ListingType.RENT,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=6500, currency="USD", period="per month"),
        "bedrooms": 2,
        "bathrooms": 2,
        "toilets": 3,
        "size_sqm": 145,
        "floor": 3,
        "total_floors": 10,
        "year_built": 2020,
        "parking_spaces": 1,
        "location": Location(
            address="1200 Ocean Ave",
            city="Santa Monica",
            state="CA",
            neighborhood="Downtown",
            lat=34.0125,
            lng=-118.4975,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["modern_living"], alt="Living room", public_id="lux4"),
            ImageItem(url=SAMPLE_IMAGES["bedroom"], alt="Bedroom", public_id="lux4a"),
        ],
        "amenities": [
            AmenityItem(name="Swimming Pool", icon="droplet"),
            AmenityItem(name="Gym", icon="activity"),
            AmenityItem(name="CCTV Security", icon="shield"),
            AmenityItem(name="Gen Set", icon="zap"),
        ],
        "features": ["Fitted kitchen", "Balcony", "Air conditioning", "Tiled throughout"],
        "is_featured": False,
        "is_new": False,
        "tags": ["rent", "santa monica", "modern", "beach"],
        "agent_name": "Sarah Connor",
        "agent_phone": "+1 310 555 9012",
    },
    {
        "title": "Star Island Estate — Grand Villa",
        "slug": "star-island-grand-villa",
        "description": "One of Miami's most prestigious addresses. This magnificent villa on Star Island sits on a 2,000sqm plot and features sweeping lawns, a bay-view master suite, six-car garage, and the finest finishes available.",
        "listing_type": ListingType.BUY,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=28500000, currency="USD"),
        "bedrooms": 7,
        "bathrooms": 8,
        "toilets": 10,
        "size_sqm": 1200,
        "year_built": 2019,
        "parking_spaces": 6,
        "location": Location(
            address="22 Star Island Dr",
            city="Miami Beach",
            state="FL",
            neighborhood="Star Island",
            lat=25.7770,
            lng=-80.1500,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["luxury_apt"], alt="Villa exterior", public_id="lux5"),
            ImageItem(url=SAMPLE_IMAGES["pool"], alt="Pool area", public_id="lux5a"),
            ImageItem(url=SAMPLE_IMAGES["lobby"], alt="Grand entrance", public_id="lux5b"),
        ],
        "amenities": [
            AmenityItem(name="Private Pool", icon="droplet"),
            AmenityItem(name="Home Cinema", icon="film"),
            AmenityItem(name="Gym & Spa", icon="activity"),
            AmenityItem(name="Staff Quarters", icon="home"),
            AmenityItem(name="Smart Home", icon="cpu"),
            AmenityItem(name="Tennis Court", icon="circle"),
            AmenityItem(name="Generator House", icon="zap"),
            AmenityItem(name="Borehole", icon="droplet"),
        ],
        "features": ["Lagoon views", "6-car garage", "Imported fixtures", "Home automation", "CCTV system", "Landscaped gardens"],
        "is_featured": True,
        "is_new": False,
        "tags": ["miami", "villa", "ultra luxury", "waterfront"],
        "agent_name": "Antonio Montana",
        "agent_phone": "+1 305 555 5678",
    },
    {
        "title": "Georgetown — Executive 4 Bedroom",
        "slug": "georgetown-executive-4-bedroom",
        "description": "Premium apartments in the heart of DC. Close to the seat of power, these executive apartments are ideal for diplomats, senior officials, and top executives seeking prime Georgetown real estate.",
        "listing_type": ListingType.BOTH,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=2800000, currency="USD"),
        "bedrooms": 4,
        "bathrooms": 4,
        "toilets": 5,
        "size_sqm": 320,
        "floor": 6,
        "total_floors": 15,
        "year_built": 2021,
        "parking_spaces": 2,
        "location": Location(
            address="1000 Potomac St NW",
            city="Washington",
            state="DC",
            neighborhood="Georgetown",
            lat=38.9051,
            lng=-77.0628,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["bedroom"], alt="Master bedroom", public_id="lux6"),
            ImageItem(url=SAMPLE_IMAGES["kitchen"], alt="Kitchen", public_id="lux6a"),
        ],
        "amenities": [
            AmenityItem(name="Swimming Pool", icon="droplet"),
            AmenityItem(name="Gym", icon="activity"),
            AmenityItem(name="24/7 Security", icon="shield"),
            AmenityItem(name="Standby Generator", icon="zap"),
            AmenityItem(name="Water Borehole", icon="droplet"),
        ],
        "features": ["City views", "Servant quarters", "Fitted kitchen", "AC throughout"],
        "is_featured": True,
        "is_new": True,
        "tags": ["dc", "georgetown", "executive", "diplomat"],
        "agent_name": "Olivia Pope",
        "agent_phone": "+1 202 555 2109",
    },
    {
        "title": "Austin Skyline — Sky Residence",
        "slug": "austin-skyline-sky-residence",
        "description": "Rising above Austin's exclusive downtown, Sky Residence offers a refined living experience with floor-to-ceiling windows, wrap-around terraces, and curated luxury throughout. Minutes from the river and finest shopping.",
        "listing_type": ListingType.RENT,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=12000, currency="USD", period="per month"),
        "service_charge": PriceDetail(amount=300, currency="USD", period="per month"),
        "bedrooms": 4,
        "bathrooms": 5,
        "toilets": 5,
        "size_sqm": 380,
        "floor": 12,
        "total_floors": 20,
        "year_built": 2022,
        "parking_spaces": 3,
        "location": Location(
            address="200 Congress Ave",
            city="Austin",
            state="TX",
            neighborhood="Downtown",
            lat=30.2640,
            lng=-97.7430,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["terrace"], alt="Terrace view", public_id="lux7"),
            ImageItem(url=SAMPLE_IMAGES["modern_living"], alt="Living area", public_id="lux7a"),
        ],
        "amenities": [
            AmenityItem(name="Rooftop Lounge", icon="sun"),
            AmenityItem(name="Pool Deck", icon="droplet"),
            AmenityItem(name="Concierge", icon="briefcase"),
            AmenityItem(name="Valet Parking", icon="car"),
            AmenityItem(name="Gym", icon="activity"),
        ],
        "features": ["Ocean views", "Wine storage", "Smart controls", "Walk-in closets", "Wrap-around terrace"],
        "is_featured": False,
        "is_new": True,
        "tags": ["austin", "luxury rental", "city view", "executive"],
        "agent_name": "Matthew McConaughey",
        "agent_phone": "+1 512 555 1098",
    },
    {
        "title": "Beverly Hills Gardens — Diplomatic Suite",
        "slug": "beverly-hills-gardens-diplomatic-suite",
        "description": "Nestled in Los Angeles' most prestigious zone, Beverly Hills Gardens offers serene luxury living surrounded by manicured gardens and excellent security. Ideal for stars and top-tier executives.",
        "listing_type": ListingType.RENT,
        "status": ListingStatus.AVAILABLE,
        "price": PriceDetail(amount=45000, currency="USD", period="per month"),
        "bedrooms": 5,
        "bathrooms": 5,
        "toilets": 6,
        "size_sqm": 450,
        "year_built": 2018,
        "parking_spaces": 4,
        "location": Location(
            address="90210 Rodeo Dr",
            city="Beverly Hills",
            state="CA",
            neighborhood="Beverly Hills",
            lat=34.0736,
            lng=-118.4004,
        ),
        "images": [
            ImageItem(url=SAMPLE_IMAGES["luxury_apt"], alt="Exterior", public_id="lux8"),
            ImageItem(url=SAMPLE_IMAGES["pool"], alt="Pool", public_id="lux8a"),
        ],
        "amenities": [
            AmenityItem(name="Gardens", icon="leaf"),
            AmenityItem(name="Pool", icon="droplet"),
            AmenityItem(name="Security Post", icon="shield"),
            AmenityItem(name="2 BQ", icon="home"),
            AmenityItem(name="Generator", icon="zap"),
        ],
        "features": ["Diplomatic zone", "6-car parking", "DSS verified", "Solar + grid power"],
        "is_featured": False,
        "is_new": False,
        "tags": ["beverly hills", "diplomatic", "la", "garden"],
        "agent_name": "Ari Gold",
        "agent_phone": "+1 310 555 0123",
    },
]


async def seed_listings() -> int:
    """Seed sample listings into the database"""
    count = 0
    for data in SEED_LISTINGS:
        existing = await Listing.find_one(Listing.slug == data["slug"])
        if not existing:
            listing = Listing(**data)
            await listing.insert()
            count += 1
    return count
