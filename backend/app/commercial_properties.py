"""Commercial property listings from JLL, CBRE, Savills and other brokerages."""

from __future__ import annotations

import hashlib
import math
import random
from typing import Any

from app.commercial_properties_data import (
    AVAILABILITY_LABELS,
    CITY_COMMERCIAL_LISTINGS,
    COMMERCIAL_BROKERS,
    GOOGLE_PROPERTY_QUERIES,
    PROPERTY_TYPE_LABELS,
)
from app.google_maps import GOOGLE_MAPS_API_KEY, get_google_api_status, search_places

BROKER_IDS = list(COMMERCIAL_BROKERS.keys())
BROKER_NAMES = [b["name"] for b in COMMERCIAL_BROKERS.values()]


def _rng(seed: str) -> random.Random:
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    return random.Random(h)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _compute_meller_fit(
    size_sqm: float,
    rent_eur_monthly: float,
    foot_traffic: float,
    tourist_index: float,
    property_type: str,
    target_size: float = 80,
) -> float:
    """Score 0-100 how suitable a unit is for a MELLER Factory store."""
    size_score = max(0, 100 - abs(size_sqm - target_size) * 1.2)
    rent_per_sqm = rent_eur_monthly / max(size_sqm, 1)
    rent_score = max(0, min(100, 100 - (rent_per_sqm - 80) * 0.8))
    location_score = foot_traffic * 0.5 + tourist_index * 0.3
    type_bonus = {"retail_high_street": 15, "unit_shop": 10, "shopping_centre": 5}.get(property_type, 0)
    return round(min(100, size_score * 0.3 + rent_score * 0.25 + location_score * 0.35 + type_bonus), 1)


def _enrich_listing(
    raw: dict,
    city: str,
    country: str,
    city_lat: float,
    city_lon: float,
    foot_traffic: float,
    tourist_index: float,
    target_size: float,
    catchment_id: str | None = None,
    street_id: str | None = None,
) -> dict[str, Any]:
    broker = COMMERCIAL_BROKERS.get(raw.get("broker_id", "local"), COMMERCIAL_BROKERS["local"])
    size = raw.get("size_sqm", 80)
    rent = raw.get("rent_eur_monthly", int(size * 95))
    prop_type = raw.get("property_type", "unit_shop")
    lat = raw["latitude"]
    lon = raw["longitude"]

    return {
        "id": raw["id"],
        "title": raw["title"],
        "address": raw["address"],
        "city": city,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "broker": broker["name"],
        "broker_id": raw.get("broker_id", "local"),
        "broker_portal": broker.get("listing_portal", broker.get("website", "")),
        "listing_url": raw.get("listing_url", broker.get("listing_portal", "")),
        "property_type": prop_type,
        "property_type_label": PROPERTY_TYPE_LABELS.get(prop_type, prop_type),
        "size_sqm": size,
        "rent_eur_monthly": rent,
        "rent_eur_sqm_year": round(rent * 12 / max(size, 1), 0),
        "availability": raw.get("availability", "available"),
        "availability_label": AVAILABILITY_LABELS.get(raw.get("availability", "available"), "Available"),
        "catchment_id": raw.get("catchment_id") or catchment_id,
        "street_id": raw.get("street_id") or street_id,
        "street_name": raw.get("street_name"),
        "catchment_name": raw.get("catchment_name"),
        "description": raw.get("description", ""),
        "meller_fit_score": _compute_meller_fit(size, rent, foot_traffic, tourist_index, prop_type, target_size),
        "distance_km": round(_haversine_km(city_lat, city_lon, lat, lon), 2),
        "data_source": raw.get("data_source", "curated"),
        "contact": raw.get("contact", f"{broker['name']} Commercial Leasing"),
    }


def _generate_synthetic_listings(
    city: str,
    country: str,
    lat: float,
    lon: float,
    city_tier: int,
    foot_traffic: float,
    tourist_index: float,
    target_size: float,
    count: int = 6,
) -> list[dict]:
    rng = _rng(f"{city}{lat}{lon}commercial")
    listings = []
    brokers = ["jll", "cbre", "savills", "cushman", "knight_frank", "colliers", "bnp"]
    types = ["retail_high_street", "unit_shop", "shopping_centre"]
    streets = [
        f"High Street {city}", f"Main Shopping Avenue", f"Central Retail Row",
        f"Fashion District", f"Old Town Market", f"Designer Boulevard",
    ]

    for i in range(count):
        broker_id = rng.choice(brokers)
        size = rng.choice([55, 65, 75, 80, 90, 100, 120, 150])
        rent_per_sqm = rng.randint(70, 180) * (1.2 if city_tier == 1 else 1.0)
        rent = int(size * rent_per_sqm)
        offset_lat = lat + rng.uniform(-0.04, 0.04)
        offset_lon = lon + rng.uniform(-0.04, 0.04)
        prop_type = rng.choice(types)
        street = streets[i % len(streets)]

        listings.append({
            "id": f"syn-{city.lower().replace(' ', '')}-{i}",
            "title": f"Retail Unit — {street}",
            "address": f"{street}, {city}",
            "latitude": round(offset_lat, 6),
            "longitude": round(offset_lon, 6),
            "broker_id": broker_id,
            "size_sqm": size,
            "rent_eur_monthly": rent,
            "property_type": prop_type,
            "availability": rng.choice(["available", "available", "available", "under_offer"]),
            "street_name": street,
            "description": f"Commercial retail unit listed via {COMMERCIAL_BROKERS[broker_id]['name']}.",
            "data_source": "synthetic",
        })
    return listings


async def _fetch_google_property_listings(
    lat: float, lon: float, city: str
) -> list[dict]:
    if not GOOGLE_MAPS_API_KEY:
        return []

    results = []
    seen: set[str] = set()
    broker_keywords = {
        "jll": "jll", "cbre": "cbre", "cushman": "cushman",
        "savills": "savills", "knight frank": "knight_frank", "colliers": "colliers",
    }

    for query in GOOGLE_PROPERTY_QUERIES[:4]:
        places = await search_places(query, lat, lon, radius_m=4000)
        for place in places:
            if place["place_id"] in seen:
                continue
            seen.add(place["place_id"])

            name_lower = (place.get("name") or "").lower()
            broker_id = "local"
            for kw, bid in broker_keywords.items():
                if kw in name_lower:
                    broker_id = bid
                    break

            size = place.get("estimated_size_sqm", 80)
            rent = int(size * random.randint(85, 160))

            results.append({
                "id": f"google-{place['place_id'][:12]}",
                "title": place.get("name", "Commercial Property"),
                "address": place.get("address", city),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "broker_id": broker_id,
                "size_sqm": size,
                "rent_eur_monthly": rent,
                "property_type": "unit_shop",
                "availability": "available",
                "description": f"Commercial listing found via Google Maps near {city}.",
                "data_source": "google_live" if place.get("data_source") == "google_live" else "google",
                "listing_url": "",
            })
    return results[:12]


def _filter_by_location(
    listings: list[dict],
    catchment_id: str | None,
    street_id: str | None,
    street_name: str | None,
    lat: float | None,
    lon: float | None,
    radius_km: float = 0.5,
) -> list[dict]:
    if catchment_id:
        matched = [l for l in listings if l.get("catchment_id") == catchment_id]
        if matched:
            return matched
    if street_id:
        matched = [l for l in listings if l.get("street_id") == street_id]
        if matched:
            return matched
    if street_name:
        matched = [l for l in listings if street_name.lower() in (l.get("street_name") or "").lower()]
        if matched:
            return matched
    if lat is not None and lon is not None:
        return [l for l in listings if _haversine_km(lat, lon, l["latitude"], l["longitude"]) <= radius_km]
    return listings


async def search_commercial_properties(
    city: str,
    country: str,
    latitude: float,
    longitude: float,
    city_tier: int,
    foot_traffic: float = 50,
    tourist_index: float = 50,
    target_size_sqm: float = 80,
    catchment_id: str | None = None,
    street_id: str | None = None,
    street_name: str | None = None,
    filter_lat: float | None = None,
    filter_lon: float | None = None,
) -> dict[str, Any]:
    """Search commercial retail listings from brokerages, linked to catchments/streets."""
    raw_listings: list[dict] = []

    curated = CITY_COMMERCIAL_LISTINGS.get(city, [])
    raw_listings.extend(curated)

    google_listings = await _fetch_google_property_listings(latitude, longitude, city)
    raw_listings.extend(google_listings)

    if len(raw_listings) < 4:
        raw_listings.extend(_generate_synthetic_listings(
            city, country, latitude, longitude, city_tier,
            foot_traffic, tourist_index, target_size_sqm,
            count=8 - len(raw_listings),
        ))

    enriched = [
        _enrich_listing(
            raw, city, country, latitude, longitude,
            foot_traffic, tourist_index, target_size_sqm,
            catchment_id=catchment_id, street_id=street_id,
        )
        for raw in raw_listings
    ]

    if catchment_id or street_id or street_name or filter_lat:
        filtered = _filter_by_location(
            enriched, catchment_id, street_id, street_name,
            filter_lat, filter_lon,
        )
        if filtered:
            enriched = filtered

    enriched.sort(key=lambda x: x["meller_fit_score"], reverse=True)

    brokers_found = sorted({l["broker"] for l in enriched})
    gstatus = get_google_api_status()

    return {
        "city": city,
        "country": country,
        "total_listings": len(enriched),
        "available_count": sum(1 for l in enriched if l["availability"] == "available"),
        "brokers": brokers_found,
        "broker_directory": [
            {**COMMERCIAL_BROKERS[bid], "id": bid}
            for bid in COMMERCIAL_BROKERS
        ],
        "listings": enriched,
        "top_pick": enriched[0] if enriched else None,
        "google_live": gstatus.get("live", False),
        "data_sources": {
            "curated": sum(1 for l in enriched if l["data_source"] == "curated"),
            "google": sum(1 for l in enriched if l["data_source"] in ("google", "google_live")),
            "synthetic": sum(1 for l in enriched if l["data_source"] == "synthetic"),
        },
        "summary": _build_summary(city, enriched, brokers_found),
    }


def _build_summary(city: str, listings: list[dict], brokers: list[str]) -> str:
    if not listings:
        return f"No commercial retail listings found for {city}."
    top = listings[0]
    avail = sum(1 for l in listings if l["availability"] == "available")
    broker_str = ", ".join(brokers[:4])
    return (
        f"{len(listings)} commercial retail units in {city} from {broker_str} "
        f"({avail} available). Top pick: {top['title']} at {top['address']} "
        f"— {top['size_sqm']}m², €{top['rent_eur_monthly']:,}/mo, "
        f"MELLER fit score {top['meller_fit_score']}/100."
    )
