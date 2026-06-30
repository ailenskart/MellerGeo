"""Google Maps / Places integration for store lookup and location intelligence."""

from __future__ import annotations

import os
from typing import Any

import httpx

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place"

MELLER_SEARCH_QUERIES = [
    "Meller sunglasses store",
    "Meller eyewear",
    "Meller optician",
]

SUNGLASSES_SEARCH_QUERIES = [
    "sunglasses store",
    "optician",
    "eyewear boutique",
    "Ray-Ban store",
    "luxury sunglasses",
]


async def search_places(
    query: str,
    latitude: float,
    longitude: float,
    radius_m: int = 5000,
) -> list[dict[str, Any]]:
    if not GOOGLE_MAPS_API_KEY:
        return _mock_places(query, latitude, longitude)

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PLACES_API_BASE}/textsearch/json",
            params={
                "query": query,
                "location": f"{latitude},{longitude}",
                "radius": radius_m,
                "key": GOOGLE_MAPS_API_KEY,
            },
        )
        data = resp.json()
        if data.get("status") != "OK":
            return _mock_places(query, latitude, longitude)

        return [_format_place(p) for p in data.get("results", [])]


async def get_place_details(place_id: str) -> dict[str, Any] | None:
    if not GOOGLE_MAPS_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{PLACES_API_BASE}/details/json",
            params={
                "place_id": place_id,
                "fields": "name,formatted_address,geometry,rating,user_ratings_total,"
                          "opening_hours,photos,website,formatted_phone_number,"
                          "business_status,types,reviews",
                "key": GOOGLE_MAPS_API_KEY,
            },
        )
        data = resp.json()
        if data.get("status") != "OK":
            return None
        return _format_place(data.get("result", {}), detailed=True)


async def find_meller_stores(latitude: float, longitude: float, city: str | None = None) -> list[dict[str, Any]]:
    from app.meller_stores import get_stores_for_city, get_all_stores

    if city:
        official = get_stores_for_city(city)
        if official:
            return [_official_store_to_place(s) for s in official]

    if GOOGLE_MAPS_API_KEY:
        results = []
        seen_ids = set()
        for query in MELLER_SEARCH_QUERIES:
            places = await search_places(query, latitude, longitude, radius_m=50000)
            for place in places:
                if place["place_id"] not in seen_ids:
                    seen_ids.add(place["place_id"])
                    results.append(place)
        if results:
            return results

    # Match by proximity to known official stores
    all_stores = get_all_stores()
    nearby = [
        s for s in all_stores
        if abs(s["latitude"] - latitude) < 0.5 and abs(s["longitude"] - longitude) < 0.5
    ]
    if nearby:
        return [_official_store_to_place(s) for s in nearby]

    return _mock_places("meller store", latitude, longitude)


def _official_store_to_place(store: dict) -> dict[str, Any]:
    return {
        "place_id": store["id"],
        "name": store["name"],
        "address": store["address"],
        "latitude": store["latitude"],
        "longitude": store["longitude"],
        "rating": 4.5,
        "user_ratings_total": 120,
        "business_status": "OPERATIONAL",
        "types": ["store", "point_of_interest"],
        "estimated_size_sqm": store["estimated_size_sqm"],
        "concept": store.get("concept"),
        "district": store.get("district"),
    }


async def find_nearby_competitors(latitude: float, longitude: float) -> list[dict[str, Any]]:
    results = []
    seen_ids = set()
    for query in SUNGLASSES_SEARCH_QUERIES:
        places = await search_places(query, latitude, longitude, radius_m=3000)
        for place in places:
            if place["place_id"] not in seen_ids:
                seen_ids.add(place["place_id"])
                results.append(place)
    return results[:20]


async def geocode_address(address: str) -> dict[str, Any] | None:
    if not GOOGLE_MAPS_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GOOGLE_MAPS_API_KEY},
        )
        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            return None
        result = data["results"][0]
        loc = result["geometry"]["location"]
        return {
            "address": result["formatted_address"],
            "latitude": loc["lat"],
            "longitude": loc["lng"],
            "place_id": result.get("place_id"),
        }


def _format_place(place: dict, detailed: bool = False) -> dict[str, Any]:
    geometry = place.get("geometry", {})
    location = geometry.get("location", {})
    return {
        "place_id": place.get("place_id", ""),
        "name": place.get("name", ""),
        "address": place.get("formatted_address", place.get("vicinity", "")),
        "latitude": location.get("lat", 0),
        "longitude": location.get("lng", 0),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("user_ratings_total", 0),
        "business_status": place.get("business_status", "OPERATIONAL"),
        "types": place.get("types", []),
        "website": place.get("website") if detailed else None,
        "phone": place.get("formatted_phone_number") if detailed else None,
        "estimated_size_sqm": _estimate_store_size(place),
    }


def _estimate_store_size(place: dict) -> int:
    """Estimate store size from place types and rating volume."""
    types = place.get("types", [])
    ratings = place.get("user_ratings_total", 0)
    if "department_store" in types:
        return 200
    if "shopping_mall" in types:
        return 150
    if ratings > 500:
        return 120
    if ratings > 100:
        return 80
    return 60


def _mock_places(query: str, lat: float, lon: float) -> list[dict[str, Any]]:
    """Fallback when no Google API key — simulated results."""
    import hashlib
    import random

    h = int(hashlib.md5(f"{query}{lat}{lon}".encode()).hexdigest()[:8], 16)
    rng = random.Random(h)

    mocks = []
    if "meller" in query.lower():
        if rng.random() > 0.6:
            mocks.append({
                "place_id": f"mock_meller_{h}",
                "name": "Meller Store",
                "address": f"Main Shopping District",
                "latitude": lat + rng.uniform(-0.01, 0.01),
                "longitude": lon + rng.uniform(-0.01, 0.01),
                "rating": round(rng.uniform(4.2, 4.8), 1),
                "user_ratings_total": rng.randint(50, 300),
                "business_status": "OPERATIONAL",
                "types": ["store", "point_of_interest"],
                "estimated_size_sqm": rng.choice([60, 80, 100, 120]),
            })
    else:
        brands = ["Ray-Ban", "Oakley", "Optical Center", "Vision Express", "Sunglass Hut"]
        for i, brand in enumerate(brands[:rng.randint(2, 5)]):
            mocks.append({
                "place_id": f"mock_comp_{h}_{i}",
                "name": f"{brand}",
                "address": f"Shopping Area {i + 1}",
                "latitude": lat + rng.uniform(-0.03, 0.03),
                "longitude": lon + rng.uniform(-0.03, 0.03),
                "rating": round(rng.uniform(3.5, 4.7), 1),
                "user_ratings_total": rng.randint(20, 500),
                "business_status": "OPERATIONAL",
                "types": ["store"],
                "estimated_size_sqm": rng.choice([50, 70, 80, 100]),
            })
    return mocks
