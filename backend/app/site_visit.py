"""Site visit intelligence — Street View, satellite, and street-level imagery."""

from __future__ import annotations

import os
from typing import Any

import httpx

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


async def get_site_visit_context(
    city: str,
    country: str,
    latitude: float,
    longitude: float,
    label: str,
    *,
    catchment_name: str | None = None,
    street_name: str | None = None,
    foot_traffic: float = 50,
    tourist_index: float = 50,
    viability_score: float = 50,
) -> dict[str, Any]:
    """Build interactive site-visit package for a location."""
    display_label = street_name or catchment_name or label

    street_view_embed = None
    street_view_static = None
    if GOOGLE_MAPS_API_KEY:
        street_view_embed = (
            f"https://www.google.com/maps/embed/v1/streetview"
            f"?key={GOOGLE_MAPS_API_KEY}&location={latitude},{longitude}"
            f"&heading=0&pitch=0&fov=90"
        )
        street_view_static = (
            f"https://maps.googleapis.com/maps/api/streetview"
            f"?size=640x400&location={latitude},{longitude}"
            f"&fov=90&heading=0&pitch=0&key={GOOGLE_MAPS_API_KEY}"
        )

    wikimedia = await _fetch_wikimedia_photos(latitude, longitude, display_label)

    return {
        "city": city,
        "country": country,
        "label": display_label,
        "latitude": latitude,
        "longitude": longitude,
        "catchment_name": catchment_name,
        "street_name": street_name,
        "foot_traffic_index": foot_traffic,
        "tourist_index": tourist_index,
        "viability_score": viability_score,
        "street_view": {
            "embed_url": street_view_embed,
            "static_image_url": street_view_static,
            "open_url": f"https://www.google.com/maps?layer=c&cbll={latitude},{longitude}",
            "available": bool(GOOGLE_MAPS_API_KEY),
        },
        "satellite": {
            "embed_url": (
                f"https://www.google.com/maps/embed/v1/view"
                f"?key={GOOGLE_MAPS_API_KEY}&center={latitude},{longitude}&zoom=18&maptype=satellite"
                if GOOGLE_MAPS_API_KEY else None
            ),
            "open_url": f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=18/{latitude}/{longitude}",
        },
        "map_links": {
            "google_maps": f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}",
            "google_earth": f"https://earth.google.com/web/search/{latitude},{longitude}",
            "openstreetmap": f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map=18/{latitude}/{longitude}",
            "mapillary": f"https://www.mapillary.com/app/?lat={latitude}&lng={longitude}&z=17",
        },
        "wikimedia_photos": wikimedia,
        "site_assessment": _build_site_assessment(
            display_label, city, foot_traffic, tourist_index, viability_score
        ),
        "expansion_checklist": _expansion_checklist(city, foot_traffic, tourist_index, viability_score),
    }


async def _fetch_wikimedia_photos(
    lat: float, lon: float, query: str, radius_m: int = 500
) -> list[dict[str, str]]:
    """Fetch nearby Creative Commons photos from Wikimedia Commons."""
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "geosearch",
                    "ggscoord": f"{lat}|{lon}",
                    "ggsradius": min(radius_m, 10000),
                    "ggslimit": 8,
                    "prop": "pageimages|coordinates|description",
                    "piprop": "thumbnail",
                    "pithumbsize": 400,
                    "format": "json",
                },
                headers={"User-Agent": "MellerGeoIntelligence/2.0"},
            )
            if resp.status_code != 200:
                return []
            pages = resp.json().get("query", {}).get("pages", {})
            photos = []
            for page in pages.values():
                thumb = page.get("thumbnail", {}).get("source")
                if thumb:
                    photos.append({
                        "title": page.get("title", "").replace("File:", ""),
                        "thumbnail_url": thumb,
                        "page_url": f"https://commons.wikimedia.org/wiki/{page.get('title', '')}",
                    })
            return photos[:6]
    except Exception:
        return []


def _build_site_assessment(
    label: str, city: str, foot_traffic: float, tourist_index: float, viability: float
) -> str:
    parts = [f"Site visit target: {label}, {city}."]
    if foot_traffic >= 75:
        parts.append("High foot traffic corridor — ideal for impulse eyewear purchases.")
    elif foot_traffic >= 50:
        parts.append("Moderate foot traffic — strong for destination shopping.")
    else:
        parts.append("Lower foot traffic — consider marketing-driven traffic generation.")

    if tourist_index >= 70:
        parts.append("Major tourist zone — summer revenue peak expected.")
    if viability >= 70:
        parts.append(f"ML viability {viability}/100 — priority expansion candidate.")
    elif viability >= 50:
        parts.append(f"ML viability {viability}/100 — validate with site visit and rent negotiation.")
    else:
        parts.append(f"ML viability {viability}/100 — proceed with caution, compare alternatives.")

    return " ".join(parts)


def _expansion_checklist(
    city: str, foot_traffic: float, tourist_index: float, viability: float
) -> list[dict[str, str]]:
    items = [
        {"item": "Verify street-level foot traffic at peak hours (12–14h, 17–20h)", "category": "visit"},
        {"item": "Check storefront visibility from main pedestrian flow", "category": "visit"},
        {"item": "Measure unit width and ceiling height (target 4m+ for MELLER Factory)", "category": "visit"},
        {"item": "Photograph competitor windows within 200m", "category": "visit"},
        {"item": "Confirm rent vs ML revenue projection", "category": "financial"},
        {"item": "Review JLL/CBRE listings in this catchment", "category": "financial"},
    ]
    if tourist_index >= 60:
        items.append({"item": "Assess tourist season signage and multilingual appeal", "category": "market"})
    if foot_traffic >= 70:
        items.append({"item": "Evaluate queue space for peak weekend traffic", "category": "operations"})
    if viability >= 65:
        items.append({"item": "Fast-track: schedule MELLER leadership site visit", "category": "action"})
    items.append({"item": f"Compare {city} against top 3 alternative cities in Compare tab", "category": "action"})
    return items


def compare_cities(
    cities: list[dict],
    store_size: float,
    predictor_predictions: list[dict],
) -> dict[str, Any]:
    """Side-by-side comparison for expansion decision-making."""
    ranked = sorted(
        zip(cities, predictor_predictions),
        key=lambda x: x[1].get("viability_score", 0),
        reverse=True,
    )

    comparison = []
    for city, pred in ranked:
        comparison.append({
            "city_id": city["id"],
            "city": city["city"],
            "country": city["country"],
            "population": city["population"],
            "gdp_per_capita": city["gdp_per_capita"],
            "city_tier": city["city_tier"],
            "foot_traffic_index": city.get("foot_traffic_index", 50),
            "tourist_index": city.get("tourist_index", 30),
            "has_existing_store": city.get("has_existing_store", False),
            "predicted_revenue_eur": pred.get("predicted_annual_revenue_eur", 0),
            "viability_score": pred.get("viability_score", 0),
            "viability_label": pred.get("viability_label", ""),
            "revenue_per_sqm": pred.get("revenue_per_sqm", 0),
            "recommendation": pred.get("recommendation", ""),
        })

    best = comparison[0] if comparison else None
    summary = (
        f"Top expansion pick: {best['city']} ({best['country']}) — "
        f"€{best['predicted_revenue_eur']:,.0f}/yr, viability {best['viability_score']}/100."
        if best else "No cities to compare."
    )

    return {
        "cities": comparison,
        "winner": best,
        "summary": summary,
        "store_size_sqm": store_size,
    }
