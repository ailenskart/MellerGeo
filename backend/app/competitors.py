"""Competitor analysis for sunglasses and eyewear brands."""

from __future__ import annotations

import hashlib
import math
import random

from app.cities_catalog import SUNGLASSES_BRANDS

BRAND_TIERS = {
    "luxury": ["Tom Ford Eyewear", "Gucci Eyewear", "Prada Eyewear", "Dior Eyewear",
               "Celine Eyewear", "Fendi Eyewear", "Versace Eyewear", "Oliver Peoples", "Persol"],
    "premium": ["Ray-Ban", "Oakley", "Maui Jim", "Gentle Monster", "Warby Parker", "Ace & Tate"],
    "mid": ["Carrera", "Police", "Vogue Eyewear", "Hawkers", "Polette", "MessyWeekend"],
    "value": ["Quay Australia", "Meller"],
}

BRAND_STORE_COUNTS = {
    "Ray-Ban": (3, 8), "Oakley": (1, 4), "Persol": (1, 3), "Gentle Monster": (0, 2),
    "Warby Parker": (0, 3), "Ace & Tate": (0, 2), "Hawkers": (1, 5), "Polette": (0, 2),
    "Meller": (0, 2), "Tom Ford Eyewear": (0, 2), "Gucci Eyewear": (1, 3),
    "Prada Eyewear": (1, 3), "Maui Jim": (0, 2), "Carrera": (1, 4),
}


def _rng_for_location(lat: float, lon: float, seed: str = "") -> random.Random:
    h = hashlib.md5(f"{lat:.4f},{lon:.4f},{seed}".encode()).hexdigest()
    return random.Random(int(h[:8], 16))


def analyze_competitors(
    city: str,
    country: str,
    latitude: float,
    longitude: float,
    population: int,
    city_tier: int,
    gdp_per_capita: float,
) -> dict:
    rng = _rng_for_location(latitude, longitude, city)

    competitors = []
    brands_present = set()

    tier_brand_map = {1: ["luxury", "premium", "mid"], 2: ["premium", "mid", "value"], 3: ["mid", "value"]}
    tiers_to_include = tier_brand_map.get(city_tier, ["mid", "value"])

    for tier_name in tiers_to_include:
        for brand in BRAND_TIERS[tier_name]:
            min_stores, max_stores = BRAND_STORE_COUNTS.get(brand, (0, 2))
            if city_tier == 1:
                count = rng.randint(max(1, min_stores), max_stores + 2)
            elif city_tier == 2:
                count = rng.randint(min_stores, max_stores)
            else:
                count = rng.randint(0, max(1, max_stores - 1))

            if count == 0 and brand != "Meller":
                continue

            for i in range(count):
                offset_lat = latitude + rng.uniform(-0.05, 0.05)
                offset_lon = longitude + rng.uniform(-0.05, 0.05)
                distance = _haversine_km(latitude, longitude, offset_lat, offset_lon)

                competitors.append({
                    "brand": brand,
                    "tier": tier_name,
                    "latitude": round(offset_lat, 6),
                    "longitude": round(offset_lon, 6),
                    "distance_km": round(distance, 2),
                    "rating": round(rng.uniform(3.5, 4.8), 1),
                    "estimated_annual_revenue_eur": _estimate_brand_revenue(
                        brand, gdp_per_capita, city_tier, rng
                    ),
                    "store_type": rng.choice(["flagship", "boutique", "department_store", "mall", "optician"]),
                })
                brands_present.add(brand)

    competitors.sort(key=lambda c: c["distance_km"])

    density = len(competitors) / max(population / 10000, 1)
    market_saturation = min(100, density * 15)

    luxury_count = sum(1 for c in competitors if c["tier"] == "luxury")
    direct_eyewear = sum(1 for c in competitors if c["brand"] in SUNGLASSES_BRANDS)

    return {
        "city": city,
        "country": country,
        "total_competitors": len(competitors),
        "brands_present": sorted(brands_present),
        "market_saturation_score": round(market_saturation, 1),
        "luxury_competitor_count": luxury_count,
        "direct_eyewear_stores": direct_eyewear,
        "nearest_competitors": competitors[:8],
        "all_competitors": competitors,
        "market_assessment": _market_assessment(market_saturation, luxury_count, city_tier),
        "meller_opportunity_score": round(
            max(0, 100 - market_saturation * 0.6 + (city_tier == 1) * 15 + (gdp_per_capita > 40000) * 10),
            1,
        ),
    }


def _estimate_brand_revenue(brand: str, gdp: float, tier: int, rng: random.Random) -> int:
    base = {"luxury": 600000, "premium": 350000, "mid": 200000, "value": 150000}
    brand_tier = next(
        (t for t, brands in BRAND_TIERS.items() if brand in brands),
        "mid",
    )
    revenue = base[brand_tier] * (gdp / 35000) ** 0.4 * (1 + tier * 0.1)
    return round(revenue * rng.uniform(0.8, 1.2), 0)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _market_assessment(saturation: float, luxury_count: int, tier: int) -> str:
    if saturation < 30 and tier <= 2:
        return "Underserved market with strong growth potential for Meller"
    if saturation < 50:
        return "Moderate competition — differentiation through brand and design will be key"
    if luxury_count >= 5:
        return "Premium-heavy market — position Meller as accessible luxury"
    return "Competitive market — focus on high-traffic locations and unique store experience"
