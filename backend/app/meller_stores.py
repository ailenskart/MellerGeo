"""Official Meller retail stores from https://mellerbrand.com/pages/our-stores"""

from __future__ import annotations

MELLER_STORES = [
    {
        "id": "meller-barcelona-portaferrissa",
        "name": "MELLER Barcelona — Portaferrissa",
        "city": "Barcelona",
        "country": "Spain",
        "address": "Calle Portaferrissa 18, Ciutat Vella, 08002 Barcelona, Spain",
        "latitude": 41.3825,
        "longitude": 2.1754,
        "estimated_size_sqm": 120,
        "opened": "2025",
        "concept": "MELLER Factory flagship",
        "district": "Gothic Quarter",
    },
    {
        "id": "meller-barcelona-argenteria",
        "name": "MELLER Barcelona — Born",
        "city": "Barcelona",
        "country": "Spain",
        "address": "Carrer de l'Argenteria 63, Ciutat Vella, 08003 Barcelona, Spain",
        "latitude": 41.3845,
        "longitude": 2.1820,
        "estimated_size_sqm": 100,
        "opened": "2025",
        "concept": "MELLER Factory — Born district",
        "district": "El Born",
    },
    {
        "id": "meller-amsterdam-kalverstraat",
        "name": "MELLER Amsterdam",
        "city": "Amsterdam",
        "country": "Netherlands",
        "address": "160 Kalverstraat, 1012 XE Amsterdam, Netherlands",
        "latitude": 52.3670,
        "longitude": 4.8900,
        "estimated_size_sqm": 110,
        "opened": "2025",
        "concept": "MELLER Factory with photo booth",
        "district": "Kalverstraat",
    },
    {
        "id": "meller-paris-rosiers",
        "name": "MELLER Paris",
        "city": "Paris",
        "country": "France",
        "address": "19 Rue des Rosiers, 75004 Paris, France",
        "latitude": 48.8570,
        "longitude": 2.3590,
        "estimated_size_sqm": 95,
        "opened": "2025",
        "concept": "MELLER Factory — Le Marais",
        "district": "Le Marais",
    },
]

MELLER_STORE_CITIES = {store["city"] for store in MELLER_STORES}

BRAND = {
    "name": "MELLER",
    "tagline": "Geo Intelligence",
    "website": "https://mellerbrand.com",
    "stores_page": "https://mellerbrand.com/pages/our-stores",
    "founded": 2014,
    "headquarters": "Barcelona, Spain",
    "customers": "3M+",
    "trustpilot": 4.4,
    "google_reviews": 4.5,
    "categories": ["Sunglasses", "Blue Light Glasses", "Watches", "Accessories"],
    "colors": {
        "orange": "#FF6723",
        "black": "#111111",
        "white": "#FFFFFF",
    },
}


def get_stores_for_city(city: str) -> list[dict]:
    return [s for s in MELLER_STORES if s["city"].lower() == city.lower()]


def get_all_stores() -> list[dict]:
    return MELLER_STORES
