"""AI verification layer — cross-checks Google Maps data with ML/synthetic signals via OpenAI."""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any

from app.competitors import analyze_competitors
from app.google_maps import GOOGLE_MAPS_API_KEY, find_meller_stores, find_nearby_competitors, get_google_api_status
from app.meller_stores import get_stores_for_city
from app.openai_client import OPENAI_API_KEY, call_openai_json
from app.social_intelligence import analyze_social_intelligence

VERIFICATION_SYSTEM_PROMPT = """You are the MELLER Geo Intelligence verification engine.
Your job is to cross-check raw data sources and produce ONE accurate, verified intelligence report.

Data sources you receive:
1. official_meller_stores — ground truth from mellerbrand.com (always trust these)
2. google_places — live Google Maps results (may include irrelevant businesses)
3. synthetic_competitors — ML-estimated competitor landscape (use as baseline, correct with Google)
4. ml_prediction — revenue model output (adjust only if Google evidence strongly contradicts)
5. social_raw — Google reviews + social signals (analyze review TEXT for real sentiment)
6. city_context — population, GDP, tier, coordinates

Rules:
- FILTER Google places: only keep eyewear/sunglasses/optician/fashion retail relevant to MELLER expansion
- REMOVE false positives (restaurants, hotels, pharmacies, generic malls with no eyewear)
- MATCH Google place names to known brands (Ray-Ban, Oakley, Sunglass Hut, Vision Express, etc.)
- RECONCILE competitor counts: prefer verified Google eyewear stores; use synthetic only to fill gaps
- VERIFY Meller stores against official list — flag if Google shows different locations
- ANALYZE review texts for genuine sentiment (not just star ratings)
- PRODUCE confidence scores 0-100 for each major conclusion
- Be conservative: when uncertain, lower confidence and note the gap
- All revenue figures in EUR
- MELLER is a Barcelona-born sunglasses brand (mellerbrand.com), positioned as accessible design-forward eyewear

Return JSON with this exact structure:
{
  "verified_meller_stores": [
    {"name": str, "address": str, "latitude": float, "longitude": float, "rating": float|null,
     "source": "official"|"google"|"both", "verified": bool, "notes": str}
  ],
  "verified_competitors": {
    "total_competitors": int,
    "brands_present": [str],
    "luxury_competitor_count": int,
    "direct_eyewear_stores": int,
    "market_saturation_score": float,
    "meller_opportunity_score": float,
    "market_assessment": str,
    "nearest_competitors": [
      {"brand": str, "tier": "luxury"|"premium"|"mid"|"value", "name": str, "address": str,
       "latitude": float, "longitude": float, "distance_km": float, "rating": float,
       "store_type": str, "source": "google"|"synthetic"|"verified", "confidence": float}
    ]
  },
  "verified_social": {
    "overall_sentiment_score": float,
    "overall_sentiment_label": str,
    "shopping_intent_score": float,
    "summary": str,
    "where_people_shop": [str],
    "top_positive_themes": [str],
    "top_negative_themes": [str],
    "review_insights": [str]
  },
  "verified_prediction": {
    "viability_score": float,
    "viability_label": str,
    "recommendation": str,
    "adjustment_notes": str,
    "confidence": float
  },
  "data_quality": {
    "google_live": bool,
    "openai_verified": true,
    "google_places_received": int,
    "google_places_kept": int,
    "warnings": [str]
  }
}"""

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_inflight: dict[str, asyncio.Task] = {}
CACHE_TTL_SECONDS = 600


def _cache_key(city_id: str, store_size: float, catchment_id: str | None, street_id: str | None) -> str:
    return f"{city_id}:{store_size}:{catchment_id or ''}:{street_id or ''}"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _prepare_raw_payload(
    city: dict,
    store_size: float,
    prediction: dict,
    *,
    area_name: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tourist_index: float = 50,
    foot_traffic: float = 50,
    meller_stores: list[dict],
    google_competitors: list[dict],
    synthetic_competitors: dict,
    social_raw: dict,
) -> dict[str, Any]:
    official = get_stores_for_city(city["city"]) or []
    return {
        "city_context": {
            "city": city["city"],
            "country": city["country"],
            "latitude": lat or city["latitude"],
            "longitude": lon or city["longitude"],
            "population": city["population"],
            "gdp_per_capita": city["gdp_per_capita"],
            "city_tier": city["city_tier"],
            "area_name": area_name or city["city"],
            "store_size_sqm": store_size,
            "tourist_index": tourist_index,
            "foot_traffic_index": foot_traffic,
        },
        "official_meller_stores": official,
        "google_meller_stores": meller_stores,
        "google_competitor_places": google_competitors[:25],
        "synthetic_competitors": {
            k: v for k, v in synthetic_competitors.items() if k != "all_competitors"
        },
        "synthetic_competitor_sample": synthetic_competitors.get("all_competitors", [])[:15],
        "ml_prediction": prediction,
        "social_raw": {
            "overall_sentiment_score": social_raw.get("overall_sentiment_score"),
            "shopping_intent_score": social_raw.get("shopping_intent_score"),
            "google": {
                "average_rating": social_raw.get("google", {}).get("average_rating"),
                "reviews": social_raw.get("google", {}).get("reviews", [])[:10],
                "top_rated_nearby": social_raw.get("google", {}).get("top_rated_nearby", []),
                "places_analyzed": social_raw.get("google", {}).get("places_analyzed", 0),
            },
            "instagram_mentions": social_raw.get("instagram", {}).get("mention_volume_monthly"),
            "twitter_mentions": social_raw.get("twitter", {}).get("mention_volume_monthly"),
            "shopping_destinations": social_raw.get("shopping_destinations", [])[:6],
            "data_sources": social_raw.get("data_sources", {}),
        },
        "data_flags": {
            "google_maps_configured": bool(GOOGLE_MAPS_API_KEY),
            "google_maps_live": get_google_api_status().get("live", False),
            "google_api_error": get_google_api_status().get("error"),
            "openai_configured": bool(OPENAI_API_KEY),
        },
    }


def _rule_based_fallback(payload: dict[str, Any]) -> dict[str, Any]:
    """Merge Google + synthetic without OpenAI when API unavailable."""
    ctx = payload["city_context"]
    lat, lon = ctx["latitude"], ctx["longitude"]
    synthetic = payload["synthetic_competitors"]
    google_places = payload["google_competitor_places"]

    eyewear_keywords = (
        "sunglass", "eyewear", "optical", "optician", "glasses", "vision",
        "ray-ban", "rayban", "oakley", "maui", "persol", "specsavers",
    )

    verified_google = []
    for place in google_places:
        name = (place.get("name") or "").lower()
        types = [t.lower() for t in place.get("types", [])]
        if any(kw in name for kw in eyewear_keywords) or "store" in types:
            dist = _haversine_km(lat, lon, place["latitude"], place["longitude"])
            verified_google.append({
                "brand": place.get("name", "Unknown"),
                "tier": "premium" if any(b in name for b in ("gucci", "prada", "dior", "tom ford")) else "mid",
                "name": place.get("name", ""),
                "address": place.get("address", ""),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "distance_km": round(dist, 2),
                "rating": place.get("rating") or 4.0,
                "store_type": "boutique",
                "source": "google",
                "confidence": 70.0,
            })

    nearest = verified_google[:8] if verified_google else synthetic.get("nearest_competitors", [])[:8]
    total = max(len(verified_google), synthetic.get("total_competitors", 0))

    official = payload["official_meller_stores"]
    meller_verified = []
    for s in official:
        meller_verified.append({
            "name": s["name"],
            "address": s["address"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "rating": 4.5,
            "source": "official",
            "verified": True,
            "notes": "Official MELLER store from mellerbrand.com",
        })

    social = payload["social_raw"]
    warnings = []
    gstatus = get_google_api_status()
    if not payload["data_flags"]["google_maps_configured"]:
        warnings.append("Google Maps API key not set — using estimated store and competitor data")
    elif not gstatus.get("live"):
        err = gstatus.get("error", "API not enabled")
        warnings.append(
            f"Google Maps live data unavailable ({err}). "
            "Enable Places API (New) in Google Cloud Console to get real store data."
        )
    if not payload["data_flags"]["openai_configured"]:
        warnings.append("OpenAI not configured — using rule-based merge only")

    return {
        "verified_meller_stores": meller_verified,
        "verified_competitors": {
            "total_competitors": total,
            "brands_present": synthetic.get("brands_present", []),
            "luxury_competitor_count": synthetic.get("luxury_competitor_count", 0),
            "direct_eyewear_stores": len(verified_google) or synthetic.get("direct_eyewear_stores", 0),
            "market_saturation_score": synthetic.get("market_saturation_score", 50),
            "meller_opportunity_score": synthetic.get("meller_opportunity_score", 60),
            "market_assessment": synthetic.get("market_assessment", ""),
            "nearest_competitors": nearest,
        },
        "verified_social": {
            "overall_sentiment_score": social.get("overall_sentiment_score", 70),
            "overall_sentiment_label": "Positive",
            "shopping_intent_score": social.get("shopping_intent_score", 60),
            "summary": f"Rule-based analysis for {ctx['area_name']}, {ctx['city']}.",
            "where_people_shop": [d.get("name", "") for d in social.get("shopping_destinations", [])[:5]],
            "top_positive_themes": ["Shopping atmosphere", "Eyewear selection"],
            "top_negative_themes": [],
            "review_insights": [],
        },
        "verified_prediction": {
            "viability_score": payload["ml_prediction"].get("viability_score", 50),
            "viability_label": payload["ml_prediction"].get("viability_label", "Moderate Potential"),
            "recommendation": payload["ml_prediction"].get("recommendation", ""),
            "adjustment_notes": "No AI adjustment applied",
            "confidence": 55.0,
        },
        "data_quality": {
            "google_live": payload["data_flags"]["google_maps_configured"],
            "openai_verified": False,
            "google_places_received": len(google_places),
            "google_places_kept": len(verified_google),
            "warnings": warnings,
        },
    }


async def build_verified_intelligence(
    city: dict,
    store_size: float,
    prediction: dict,
    *,
    catchment_id: str | None = None,
    street_id: str | None = None,
    area_name: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tourist_index: float = 50,
    foot_traffic: float = 50,
    skip_ai: bool = False,
) -> dict[str, Any]:
    """Gather all sources, verify via OpenAI, return unified intelligence."""
    key = _cache_key(city["id"], store_size, catchment_id, street_id)
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    if key in _inflight:
        return await _inflight[key]

    task = asyncio.create_task(
        _build_verified_intelligence_inner(
            city, store_size, prediction,
            catchment_id=catchment_id, street_id=street_id,
            area_name=area_name, lat=lat, lon=lon,
            tourist_index=tourist_index, foot_traffic=foot_traffic,
            skip_ai=skip_ai, cache_key=key,
        )
    )
    _inflight[key] = task
    try:
        return await task
    finally:
        _inflight.pop(key, None)


async def _build_verified_intelligence_inner(
    city: dict,
    store_size: float,
    prediction: dict,
    *,
    catchment_id: str | None,
    street_id: str | None,
    area_name: str | None,
    lat: float | None,
    lon: float | None,
    tourist_index: float,
    foot_traffic: float,
    skip_ai: bool,
    cache_key: str,
) -> dict[str, Any]:
    use_lat = lat or city["latitude"]
    use_lon = lon or city["longitude"]

    meller_stores = await find_meller_stores(use_lat, use_lon, city=city["city"])
    google_competitors = await find_nearby_competitors(use_lat, use_lon)

    synthetic = analyze_competitors(
        city=city["city"],
        country=city["country"],
        latitude=use_lat,
        longitude=use_lon,
        population=city["population"],
        city_tier=city["city_tier"],
        gdp_per_capita=city["gdp_per_capita"],
    )

    social_raw = await analyze_social_intelligence(
        city=city["city"],
        country=city["country"],
        latitude=use_lat,
        longitude=use_lon,
        area_name=area_name,
        tourist_index=tourist_index,
        foot_traffic=foot_traffic,
        catchment_id=catchment_id,
        street_name=area_name if street_id else None,
    )

    payload = _prepare_raw_payload(
        city, store_size, prediction,
        area_name=area_name, lat=use_lat, lon=use_lon,
        tourist_index=tourist_index, foot_traffic=foot_traffic,
        meller_stores=meller_stores,
        google_competitors=google_competitors,
        synthetic_competitors=synthetic,
        social_raw=social_raw,
    )

    verified = None
    if not skip_ai and OPENAI_API_KEY:
        verified = await call_openai_json(VERIFICATION_SYSTEM_PROMPT, payload)
    if not verified:
        verified = _rule_based_fallback(payload)
    else:
        verified.setdefault("data_quality", {})
        verified["data_quality"]["openai_verified"] = True
        verified["data_quality"]["google_live"] = get_google_api_status().get("live", False)

    result = {
        "verified": verified,
        "raw": {
            "meller_stores": meller_stores,
            "google_competitors": google_competitors,
            "synthetic_competitors": synthetic,
            "social_raw": social_raw,
        },
    }

    _cache[cache_key] = (time.time(), result)
    return result


async def build_city_intelligence_bundle(
    city: dict,
    store_size: float,
    prediction: dict,
    seasonality: dict,
    *,
    catchment_id: str | None = None,
    street_id: str | None = None,
    area_name: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    tourist_index: float = 50,
    foot_traffic: float = 50,
) -> dict[str, Any]:
    """Single call that returns competitors, stores, social — one AI verification pass."""
    intel = await build_verified_intelligence(
        city, store_size, prediction,
        catchment_id=catchment_id, street_id=street_id,
        area_name=area_name, lat=lat, lon=lon,
        tourist_index=tourist_index, foot_traffic=foot_traffic,
    )
    import os
    return {
        "competitors": apply_verified_competitors(intel["verified"], city),
        "stores": apply_verified_stores(intel, bool(os.getenv("GOOGLE_MAPS_API_KEY"))),
        "social": apply_verified_social(intel, city),
        "seasonality": seasonality,
        "google_status": get_google_api_status(),
    }


def apply_verified_competitors(verified: dict[str, Any], city: dict) -> dict[str, Any]:
    comp = verified["verified_competitors"]
    nearest = []
    for c in comp.get("nearest_competitors", [])[:8]:
        nearest.append({
            "brand": c.get("brand", c.get("name", "Unknown")),
            "tier": c.get("tier", "mid"),
            "latitude": c.get("latitude", city["latitude"]),
            "longitude": c.get("longitude", city["longitude"]),
            "distance_km": c.get("distance_km", 0),
            "rating": c.get("rating", 4.0),
            "estimated_annual_revenue_eur": c.get("estimated_annual_revenue_eur", 250000),
            "store_type": c.get("store_type", "boutique"),
        })
    return {
        "city": city["city"],
        "country": city["country"],
        **{k: comp[k] for k in (
            "total_competitors", "brands_present", "market_saturation_score",
            "luxury_competitor_count", "direct_eyewear_stores",
            "market_assessment", "meller_opportunity_score",
        ) if k in comp},
        "nearest_competitors": nearest,
        "ai_verified": verified.get("data_quality", {}).get("openai_verified", False),
        "verification_confidence": _avg_competitor_confidence(comp),
        "data_quality": verified.get("data_quality", {}),
    }


def _avg_competitor_confidence(comp: dict) -> float:
    confs = [c.get("confidence", 70) for c in comp.get("nearest_competitors", []) if c.get("confidence")]
    return round(sum(confs) / len(confs), 1) if confs else 70.0


def apply_verified_stores(verified_intel: dict[str, Any], google_enabled: bool) -> dict[str, Any]:
    verified = verified_intel["verified"]
    raw = verified_intel["raw"]
    meller = []
    for s in verified.get("verified_meller_stores", []):
        meller.append({
            "place_id": s.get("place_id", f"verified_{s.get('name', '')}"),
            "name": s["name"],
            "address": s["address"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "rating": s.get("rating"),
            "user_ratings_total": s.get("user_ratings_total", 0),
            "business_status": "OPERATIONAL",
            "types": ["store"],
            "estimated_size_sqm": s.get("estimated_size_sqm", 80),
            "verified": s.get("verified", True),
            "source": s.get("source", "official"),
        })

    if not meller:
        meller = raw["meller_stores"]

    competitors = []
    for c in verified.get("verified_competitors", {}).get("nearest_competitors", []):
        if c.get("source") in ("google", "verified"):
            competitors.append({
                "place_id": c.get("place_id", f"comp_{c.get('name', '')}"),
                "name": c.get("name", c.get("brand", "")),
                "address": c.get("address", ""),
                "latitude": c.get("latitude", 0),
                "longitude": c.get("longitude", 0),
                "rating": c.get("rating"),
                "user_ratings_total": 0,
                "business_status": "OPERATIONAL",
                "types": ["store"],
                "estimated_size_sqm": 80,
            })

    if not competitors:
        competitors = raw["google_competitors"][:12]

    return {
        "meller_stores": meller,
        "nearby_competitors": competitors,
        "google_maps_enabled": google_enabled,
        "ai_verified": verified.get("data_quality", {}).get("openai_verified", False),
        "data_quality": verified.get("data_quality", {}),
    }


def apply_verified_social(verified_intel: dict[str, Any], city: dict) -> dict[str, Any]:
    verified = verified_intel["verified"]
    raw_social = verified_intel["raw"]["social_raw"]
    vsocial = verified.get("verified_social", {})

    result = dict(raw_social)
    result["overall_sentiment_score"] = vsocial.get("overall_sentiment_score", result.get("overall_sentiment_score"))
    result["overall_sentiment_label"] = vsocial.get("overall_sentiment_label", result.get("overall_sentiment_label"))
    result["shopping_intent_score"] = vsocial.get("shopping_intent_score", result.get("shopping_intent_score"))
    result["summary"] = vsocial.get("summary", result.get("summary"))
    result["where_people_shop"] = vsocial.get("where_people_shop", result.get("where_people_shop", []))
    result["top_positive_themes"] = vsocial.get("top_positive_themes", result.get("top_positive_themes", []))
    result["top_negative_themes"] = vsocial.get("top_negative_themes", result.get("top_negative_themes", []))
    result["ai_verified"] = verified.get("data_quality", {}).get("openai_verified", False)
    result["review_insights"] = vsocial.get("review_insights", [])
    result["data_quality"] = verified.get("data_quality", {})
    return result


def build_chat_context(verified_intel: dict[str, Any], city: dict, prediction: dict, seasonality: dict, market_insights: dict) -> dict[str, Any]:
    verified = verified_intel["verified"]
    vp = verified.get("verified_prediction", {})
    return {
        "selected_city": city,
        "prediction": {
            **prediction,
            "viability_score": vp.get("viability_score", prediction.get("viability_score")),
            "viability_label": vp.get("viability_label", prediction.get("viability_label")),
            "recommendation": vp.get("recommendation", prediction.get("recommendation")),
            "ai_adjustment_notes": vp.get("adjustment_notes", ""),
            "confidence": vp.get("confidence", 70),
        },
        "competitors": apply_verified_competitors(verified, city),
        "seasonality": seasonality,
        "market_insights": market_insights,
        "meller_stores": verified.get("verified_meller_stores", verified_intel["raw"]["meller_stores"]),
        "social_intelligence": verified.get("verified_social", {}),
        "verification": verified.get("data_quality", {}),
        "ai_verified": verified.get("data_quality", {}).get("openai_verified", False),
    }
