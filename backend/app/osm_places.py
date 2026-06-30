"""OpenStreetMap fallback for store/retail search when Google Maps is unavailable."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = "MellerGeoIntelligence/2.0 (store expansion research)"

EYEWEAR_SHOP_TAGS = [
    "optician", "sunglasses", "beauty", "clothes", "fashion", "jewelry",
    "boutique", "gift", "mall",
]


async def search_osm_places(
    query: str,
    latitude: float,
    longitude: float,
    radius_m: int = 3000,
    limit: int = 15,
) -> list[dict[str, Any]]:
    """Find retail shops near coordinates via Overpass API."""
    is_eyewear_query = any(
        kw in query.lower()
        for kw in ("sunglass", "eyewear", "optician", "meller", "glasses", "optical")
    )
    shop_filter = "optician|beauty|clothes|fashion|jewelry|gift" if is_eyewear_query else "clothes|fashion|beauty|mall|department_store|jewelry"

    overpass_query = f"""
    [out:json][timeout:20];
    (
      node["shop"~"{shop_filter}"](around:{radius_m},{latitude},{longitude});
      way["shop"~"{shop_filter}"](around:{radius_m},{latitude},{longitude});
      node["name"~"{_escape_regex(query[:40])}",i](around:{radius_m},{latitude},{longitude});
    );
    out center {limit};
  """

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(
                OVERPASS_URL,
                data={"data": overpass_query},
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200:
                return await _nominatim_search(query, latitude, longitude, limit)

            elements = resp.json().get("elements", [])
            results = []
            seen: set[str] = set()

            for el in elements:
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("brand") or tags.get("operator")
                if not name:
                    continue

                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if lat is None or lon is None:
                    continue

                key = f"{name}:{lat:.4f}:{lon:.4f}"
                if key in seen:
                    continue
                seen.add(key)

                street = tags.get("addr:street", "")
                housenumber = tags.get("addr:housenumber", "")
                city = tags.get("addr:city", "")
                address = ", ".join(p for p in [f"{street} {housenumber}".strip(), city] if p) or tags.get("addr:full", "")

                results.append({
                    "place_id": f"osm_{el.get('type', 'node')}_{el.get('id', '')}",
                    "name": name,
                    "address": address or f"Near {query}",
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "rating": None,
                    "user_ratings_total": 0,
                    "business_status": "OPERATIONAL",
                    "types": [tags.get("shop", "store")],
                    "estimated_size_sqm": 80,
                    "data_source": "osm_live",
                    "brand": tags.get("brand", ""),
                    "shop_type": tags.get("shop", ""),
                })

            if results:
                return results[:limit]
            return await _nominatim_search(query, latitude, longitude, limit)
    except Exception:
        return await _nominatim_search(query, latitude, longitude, limit)


async def _nominatim_search(
    query: str, latitude: float, longitude: float, limit: int
) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={
                    "q": f"{query} near {latitude},{longitude}",
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                },
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200:
                return []

            results = []
            for item in resp.json():
                name = item.get("display_name", "").split(",")[0]
                results.append({
                    "place_id": f"osm_nominatim_{item.get('osm_id', '')}",
                    "name": name or query,
                    "address": item.get("display_name", ""),
                    "latitude": float(item.get("lat", latitude)),
                    "longitude": float(item.get("lon", longitude)),
                    "rating": None,
                    "user_ratings_total": 0,
                    "business_status": "OPERATIONAL",
                    "types": [item.get("type", "shop")],
                    "estimated_size_sqm": 80,
                    "data_source": "osm_live",
                })
            return results
    except Exception:
        return []


async def geocode_osm(address: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                NOMINATIM_URL,
                params={"q": address, "format": "json", "limit": 1},
                headers={"User-Agent": USER_AGENT},
            )
            if resp.status_code != 200 or not resp.json():
                return None
            item = resp.json()[0]
            return {
                "address": item.get("display_name", address),
                "latitude": float(item.get("lat", 0)),
                "longitude": float(item.get("lon", 0)),
                "place_id": f"osm_{item.get('osm_id', '')}",
            }
    except Exception:
        return None


async def probe_osm_api() -> bool:
    try:
        results = await search_osm_places("optician", 41.3851, 2.1734, radius_m=2000, limit=3)
        return len(results) > 0
    except Exception:
        return False


def _escape_regex(s: str) -> str:
    return re.sub(r"[.*+?^${}()|[\]\\]", "", s)[:30]
