"""Google Maps / Places integration — Places API (New) only."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
PLACES_NEW_BASE = "https://places.googleapis.com/v1"

_google_api_status: dict[str, Any] = {
    "configured": bool(GOOGLE_MAPS_API_KEY),
    "live": False,
    "google_live": False,
    "osm_live": False,
    "live_source": None,
    "api_used": None,
    "error": None,
    "enable_url": "https://console.cloud.google.com/apis/library/places.googleapis.com",
    "fix_instructions": None,
}

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

SEARCH_FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.rating,places.userRatingCount,places.businessStatus,places.types"
)

DETAILS_FIELD_MASK = (
    "id,displayName,formattedAddress,location,rating,userRatingCount,"
    "businessStatus,types,reviews,websiteUri,nationalPhoneNumber"
)


def get_google_api_status() -> dict[str, Any]:
    return dict(_google_api_status)


def _parse_enable_url(error_message: str) -> str:
    match = re.search(r"project\s+(\d+)", error_message)
    if match:
        return f"https://console.developers.google.com/apis/api/places.googleapis.com/overview?project={match.group(1)}"
    return "https://console.cloud.google.com/apis/library/places.googleapis.com"


def _friendly_error(raw: str) -> str:
    lower = raw.lower()
    if "legacy" in lower or "not enabled" in lower or "disabled" in lower:
        return (
            "Places API (New) is not enabled for your Google Cloud project. "
            "Enable it using the link below — the old Places API is no longer used."
        )
    if "permission" in lower or "denied" in lower:
        return f"Google Maps access denied: {raw}"
    return raw


async def probe_google_maps_api() -> dict[str, Any]:
    """Check map data sources on startup — Google first, then OpenStreetMap fallback."""
    from app.osm_places import probe_osm_api

    google_ok = False
    if GOOGLE_MAPS_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{PLACES_NEW_BASE}/places:searchText",
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                        "X-Goog-FieldMask": "places.id",
                    },
                    json={
                        "textQuery": "sunglasses store Barcelona",
                        "locationBias": {
                            "circle": {
                                "center": {"latitude": 41.3851, "longitude": 2.1734},
                                "radius": 1000.0,
                            }
                        },
                    },
                )
                if resp.status_code == 200:
                    google_ok = True
                    _google_api_status.update({
                        "configured": True,
                        "live": True,
                        "google_live": True,
                        "osm_live": False,
                        "live_source": "google",
                        "api_used": "places_new",
                        "error": None,
                        "fix_instructions": None,
                    })
                    return get_google_api_status()
                raw = resp.json().get("error", {}).get("message", resp.text[:200])
                _google_api_status.update({
                    "configured": True,
                    "google_live": False,
                    "error": _friendly_error(raw),
                    "enable_url": _parse_enable_url(raw),
                })
        except Exception as exc:
            _google_api_status.update({"configured": True, "google_live": False, "error": str(exc)})
    else:
        _google_api_status.update({
            "configured": False,
            "error": None,
        })

    osm_ok = await probe_osm_api()
    if osm_ok:
        _google_api_status.update({
            "live": True,
            "osm_live": True,
            "live_source": "openstreetmap",
            "api_used": "osm",
            "error": None,
            "fix_instructions": None,
        })
    else:
        _google_api_status.update({
            "live": False,
            "osm_live": False,
            "live_source": None,
            "api_used": None,
            "fix_instructions": (
                "Using estimated data. Enable Places API (New) in Google Cloud for Google live data."
                if GOOGLE_MAPS_API_KEY else None
            ),
        })

    return get_google_api_status()


async def search_places(
    query: str,
    latitude: float,
    longitude: float,
    radius_m: int = 5000,
) -> list[dict[str, Any]]:
    from app.osm_places import search_osm_places

    if GOOGLE_MAPS_API_KEY:
        places = await _search_places_new(query, latitude, longitude, radius_m)
        if places is not None and places:
            return places

    osm_places = await search_osm_places(query, latitude, longitude, radius_m=min(radius_m, 3000))
    if osm_places:
        _google_api_status.update({
            "live": True,
            "osm_live": True,
            "live_source": "openstreetmap",
            "api_used": "osm",
            "error": None,
        })
        return osm_places

    return _mock_places(query, latitude, longitude)


async def _search_places_new(
    query: str, latitude: float, longitude: float, radius_m: int
) -> list[dict[str, Any]] | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{PLACES_NEW_BASE}/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                    "X-Goog-FieldMask": SEARCH_FIELD_MASK,
                },
                json={
                    "textQuery": query,
                    "locationBias": {
                        "circle": {
                            "center": {"latitude": latitude, "longitude": longitude},
                            "radius": float(radius_m),
                        }
                    },
                },
            )
            if resp.status_code != 200:
                raw = resp.json().get("error", {}).get("message", resp.text[:200])
                if not _google_api_status.get("osm_live"):
                    _google_api_status.update({
                        "configured": True,
                        "live": False,
                        "google_live": False,
                        "api_used": "places_new",
                        "error": _friendly_error(raw),
                        "enable_url": _parse_enable_url(raw),
                    })
                return None

            results = [_format_place_new(p) for p in resp.json().get("places", [])]
            if results:
                _google_api_status.update({
                    "configured": True,
                    "live": True,
                    "google_live": True,
                    "live_source": "google",
                    "api_used": "places_new",
                    "error": None,
                })
            return results
    except Exception as exc:
        _google_api_status.update({
            "configured": True,
            "live": False,
            "error": str(exc),
        })
        return None


async def get_place_details(place_id: str) -> dict[str, Any] | None:
    if not GOOGLE_MAPS_API_KEY or place_id.startswith("mock_"):
        return None

    resource = place_id if place_id.startswith("places/") else f"places/{place_id}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{PLACES_NEW_BASE}/{resource}",
                headers={
                    "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                    "X-Goog-FieldMask": DETAILS_FIELD_MASK,
                },
            )
            if resp.status_code == 200:
                return _format_place_new(resp.json(), detailed=True)
    except Exception:
        pass
    return None


async def find_meller_stores(latitude: float, longitude: float, city: str | None = None) -> list[dict[str, Any]]:
    from app.meller_stores import get_all_stores, get_stores_for_city

    if city:
        official = get_stores_for_city(city)
        if official:
            return [_official_store_to_place(s) for s in official]

    if _google_api_status.get("live") or GOOGLE_MAPS_API_KEY:
        results = []
        seen_ids: set[str] = set()
        for q in MELLER_SEARCH_QUERIES:
            places = await search_places(q, latitude, longitude, radius_m=50000)
            for place in places:
                if place["place_id"] not in seen_ids and place.get("data_source") in ("google_live", "osm_live"):
                    seen_ids.add(place["place_id"])
                    results.append(place)
        if results:
            return results

    all_stores = get_all_stores()
    nearby = [
        s for s in all_stores
        if abs(s["latitude"] - latitude) < 0.5 and abs(s["longitude"] - longitude) < 0.5
    ]
    if nearby:
        return [_official_store_to_place(s) for s in nearby]

    return []


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
        "data_source": "official",
    }


async def find_nearby_competitors(latitude: float, longitude: float) -> list[dict[str, Any]]:
    results = []
    seen_ids: set[str] = set()
    for query in SUNGLASSES_SEARCH_QUERIES:
        places = await search_places(query, latitude, longitude, radius_m=3000)
        for place in places:
            if place["place_id"] not in seen_ids:
                seen_ids.add(place["place_id"])
                results.append(place)
    return results[:20]


async def geocode_address(address: str) -> dict[str, Any] | None:
    """Geocode via Places API (New) search — no legacy Geocoding API needed."""
    if not GOOGLE_MAPS_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{PLACES_NEW_BASE}/places:searchText",
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
                    "X-Goog-FieldMask": "places.id,places.formattedAddress,places.location",
                },
                json={"textQuery": address},
            )
            if resp.status_code != 200:
                return None
            places = resp.json().get("places", [])
            if not places:
                return None
            p = places[0]
            loc = p.get("location", {})
            return {
                "address": p.get("formattedAddress", address),
                "latitude": loc.get("latitude", 0),
                "longitude": loc.get("longitude", 0),
                "place_id": p.get("id", ""),
            }
    except Exception:
        return None


def _format_place_new(place: dict, detailed: bool = False) -> dict[str, Any]:
    loc = place.get("location", {})
    name = place.get("displayName", {})
    reviews_raw = place.get("reviews", []) if detailed else []
    reviews = []
    for r in reviews_raw:
        reviews.append({
            "author": r.get("authorAttribution", {}).get("displayName", "Anonymous"),
            "rating": r.get("rating"),
            "text": r.get("text", {}).get("text", r.get("originalText", {}).get("text", "")),
            "time": r.get("relativePublishTimeDescription", ""),
            "source": "google",
        })

    pid = place.get("id", place.get("name", ""))
    return {
        "place_id": pid,
        "name": name.get("text", "") if isinstance(name, dict) else str(name),
        "address": place.get("formattedAddress", ""),
        "latitude": loc.get("latitude", 0),
        "longitude": loc.get("longitude", 0),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("userRatingCount", 0),
        "business_status": place.get("businessStatus", "OPERATIONAL"),
        "types": place.get("types", []),
        "website": place.get("websiteUri") if detailed else None,
        "phone": place.get("nationalPhoneNumber") if detailed else None,
        "estimated_size_sqm": _estimate_store_size({
            "types": place.get("types", []),
            "user_ratings_total": place.get("userRatingCount", 0),
        }),
        "data_source": "google_live",
        "reviews": reviews,
    }


def _estimate_store_size(place: dict) -> int:
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
                "address": "Main Shopping District",
                "latitude": lat + rng.uniform(-0.01, 0.01),
                "longitude": lon + rng.uniform(-0.01, 0.01),
                "rating": round(rng.uniform(4.2, 4.8), 1),
                "user_ratings_total": rng.randint(50, 300),
                "business_status": "OPERATIONAL",
                "types": ["store", "point_of_interest"],
                "estimated_size_sqm": rng.choice([60, 80, 100, 120]),
                "data_source": "mock",
            })
    else:
        brands = ["Ray-Ban", "Oakley", "Optical Center", "Vision Express", "Sunglass Hut"]
        for i, brand in enumerate(brands[:rng.randint(2, 5)]):
            mocks.append({
                "place_id": f"mock_comp_{h}_{i}",
                "name": brand,
                "address": f"Shopping Area {i + 1}",
                "latitude": lat + rng.uniform(-0.03, 0.03),
                "longitude": lon + rng.uniform(-0.03, 0.03),
                "rating": round(rng.uniform(3.5, 4.7), 1),
                "user_ratings_total": rng.randint(20, 500),
                "business_status": "OPERATIONAL",
                "types": ["store"],
                "estimated_size_sqm": rng.choice([50, 70, 80, 100]),
                "data_source": "mock",
            })
    return mocks
