"""Generate realistic synthetic training data for Meller European stores."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.features import FEATURE_COLUMNS

RNG = np.random.default_rng(42)

EUROPE_CITIES = [
    {"city": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "pop": 3_280_000, "gdp": 32_500, "tier": 1},
    {"city": "Barcelona", "country": "Spain", "lat": 41.3851, "lon": 2.1734, "pop": 1_620_000, "gdp": 34_200, "tier": 1},
    {"city": "Valencia", "country": "Spain", "lat": 39.4699, "lon": -0.3763, "pop": 800_000, "gdp": 28_100, "tier": 2},
    {"city": "Seville", "country": "Spain", "lat": 37.3891, "lon": -5.9845, "pop": 690_000, "gdp": 24_800, "tier": 2},
    {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "pop": 2_160_000, "gdp": 42_800, "tier": 1},
    {"city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "pop": 520_000, "gdp": 36_500, "tier": 2},
    {"city": "Marseille", "country": "France", "lat": 43.2965, "lon": 5.3698, "pop": 870_000, "gdp": 29_400, "tier": 2},
    {"city": "Nice", "country": "France", "lat": 43.7102, "lon": 7.2620, "pop": 340_000, "gdp": 33_600, "tier": 2},
    {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "pop": 3_650_000, "gdp": 38_200, "tier": 1},
    {"city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820, "pop": 1_480_000, "gdp": 52_400, "tier": 1},
    {"city": "Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937, "pop": 1_840_000, "gdp": 45_100, "tier": 1},
    {"city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "pop": 750_000, "gdp": 58_300, "tier": 2},
    {"city": "Cologne", "country": "Germany", "lat": 50.9375, "lon": 6.9603, "pop": 1_080_000, "gdp": 41_200, "tier": 2},
    {"city": "Milan", "country": "Italy", "lat": 45.4642, "lon": 9.1900, "pop": 1_350_000, "gdp": 41_600, "tier": 1},
    {"city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "pop": 2_870_000, "gdp": 31_800, "tier": 1},
    {"city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "pop": 380_000, "gdp": 35_200, "tier": 2},
    {"city": "Naples", "country": "Italy", "lat": 40.8518, "lon": 14.2681, "pop": 960_000, "gdp": 22_400, "tier": 2},
    {"city": "London", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278, "pop": 8_960_000, "gdp": 48_500, "tier": 1},
    {"city": "Manchester", "country": "United Kingdom", "lat": 53.4808, "lon": -2.2426, "pop": 550_000, "gdp": 32_100, "tier": 2},
    {"city": "Edinburgh", "country": "United Kingdom", "lat": 55.9533, "lon": -3.1883, "pop": 530_000, "gdp": 38_700, "tier": 2},
    {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "pop": 870_000, "gdp": 52_800, "tier": 1},
    {"city": "Rotterdam", "country": "Netherlands", "lat": 51.9244, "lon": 4.4777, "pop": 650_000, "gdp": 44_200, "tier": 2},
    {"city": "Brussels", "country": "Belgium", "lat": 50.8503, "lon": 4.3517, "pop": 1_210_000, "gdp": 43_600, "tier": 1},
    {"city": "Antwerp", "country": "Belgium", "lat": 51.2194, "lon": 4.4025, "pop": 530_000, "gdp": 41_800, "tier": 2},
    {"city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393, "pop": 550_000, "gdp": 28_900, "tier": 1},
    {"city": "Porto", "country": "Portugal", "lat": 41.1579, "lon": -8.6291, "pop": 240_000, "gdp": 26_400, "tier": 2},
    {"city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "pop": 1_900_000, "gdp": 50_200, "tier": 1},
    {"city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417, "pop": 430_000, "gdp": 78_400, "tier": 1},
    {"city": "Geneva", "country": "Switzerland", "lat": 46.2044, "lon": 6.1432, "pop": 200_000, "gdp": 82_100, "tier": 2},
    {"city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "pop": 640_000, "gdp": 58_600, "tier": 1},
    {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "pop": 980_000, "gdp": 54_300, "tier": 1},
    {"city": "Oslo", "country": "Norway", "lat": 59.9139, "lon": 10.7522, "pop": 700_000, "gdp": 72_500, "tier": 1},
    {"city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "pop": 660_000, "gdp": 48_900, "tier": 1},
    {"city": "Dublin", "country": "Ireland", "lat": 53.3498, "lon": -6.2603, "pop": 550_000, "gdp": 78_200, "tier": 1},
    {"city": "Warsaw", "country": "Poland", "lat": 52.2297, "lon": 21.0122, "pop": 1_790_000, "gdp": 22_800, "tier": 1},
    {"city": "Krakow", "country": "Poland", "lat": 50.0647, "lon": 19.9450, "pop": 780_000, "gdp": 20_100, "tier": 2},
    {"city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "pop": 1_320_000, "gdp": 28_600, "tier": 1},
    {"city": "Budapest", "country": "Hungary", "lat": 47.4979, "lon": 19.0402, "pop": 1_750_000, "gdp": 21_400, "tier": 1},
    {"city": "Athens", "country": "Greece", "lat": 37.9838, "lon": 23.7275, "pop": 660_000, "gdp": 24_600, "tier": 1},
    {"city": "Bucharest", "country": "Romania", "lat": 44.4268, "lon": 26.1025, "pop": 1_800_000, "gdp": 16_800, "tier": 1},
]


def _derive_geo_features(city: dict, rng: np.random.Generator) -> dict:
    tier = city["tier"]
    pop = city["pop"]
    gdp = city["gdp"]

    density = pop / rng.uniform(80, 450)
    income = gdp * rng.uniform(0.65, 0.95)
    foot_traffic = min(100, 35 + tier * 15 + rng.normal(0, 8) + (gdp / 1000))
    tourist = min(100, rng.uniform(10, 90) if city["city"] in {
        "Paris", "Barcelona", "Rome", "Amsterdam", "Prague", "Vienna", "Florence", "Nice", "Lisbon", "Edinburgh"
    } else rng.uniform(5, 45))
    competitors = max(0.5, rng.normal(3.5 - tier * 0.3, 0.8))
    luxury = min(100, 30 + tier * 20 + gdp / 1200 + rng.normal(0, 6))
    transport = min(100, 40 + tier * 18 + rng.normal(0, 7))
    rent = min(100, 25 + tier * 12 + gdp / 900 + rng.normal(0, 5))
    age = rng.uniform(36, 44) if tier == 1 else rng.uniform(38, 48)
    ecommerce = min(100, 25 + gdp / 1200 + rng.normal(0, 5))
    mall = float(rng.choice([0.0, 0.3, 0.7, 1.0], p=[0.35, 0.25, 0.25, 0.15]))
    size = float(rng.choice([60, 70, 80, 100, 120], p=[0.15, 0.25, 0.35, 0.15, 0.10]))

    return {
        "city": city["city"],
        "country": city["country"],
        "latitude": city["lat"],
        "longitude": city["lon"],
        "population": pop,
        "population_density": round(density, 1),
        "gdp_per_capita": gdp,
        "avg_household_income": round(income, 0),
        "foot_traffic_index": round(foot_traffic, 1),
        "tourist_index": round(tourist, 1),
        "fashion_competitor_density": round(competitors, 2),
        "luxury_retail_proximity": round(luxury, 1),
        "public_transport_score": round(transport, 1),
        "retail_rent_index": round(rent, 1),
        "median_age": round(age, 1),
        "ecommerce_penetration": round(ecommerce, 1),
        "mall_vs_street": mall,
        "store_size_sqm": size,
        "city_tier": tier,
    }


def _compute_revenue(row: dict, rng: np.random.Generator) -> float:
    """Realistic revenue model for Meller eyewear stores (EUR/year)."""
    base = 180_000

    income_factor = (row["avg_household_income"] / 35_000) ** 0.55
    traffic_factor = (row["foot_traffic_index"] / 50) ** 0.7
    tourist_factor = 1 + (row["tourist_index"] / 100) * 0.25
    luxury_factor = 1 + (row["luxury_retail_proximity"] / 100) * 0.2
    transport_factor = 1 + (row["public_transport_score"] / 100) * 0.12
    size_factor = (row["store_size_sqm"] / 80) ** 0.35
    tier_factor = {1: 1.15, 2: 1.0, 3: 0.85}[row["city_tier"]]

    competitor_penalty = max(0.75, 1 - (row["fashion_competitor_density"] - 2) * 0.04)
    rent_penalty = max(0.82, 1 - (row["retail_rent_index"] / 100) * 0.15)
    ecommerce_penalty = max(0.78, 1 - (row["ecommerce_penetration"] / 100) * 0.22)
    mall_bonus = 1 + row["mall_vs_street"] * 0.08
    age_factor = 1 - abs(row["median_age"] - 38) * 0.008

    revenue = (
        base
        * income_factor
        * traffic_factor
        * tourist_factor
        * luxury_factor
        * transport_factor
        * size_factor
        * tier_factor
        * competitor_penalty
        * rent_penalty
        * ecommerce_penalty
        * mall_bonus
        * age_factor
    )
    noise = rng.lognormal(0, 0.08)
    return round(revenue * noise, 0)


def generate_training_data(n_per_city: int = 4) -> pd.DataFrame:
    rows = []
    for city in EUROPE_CITIES:
        for i in range(n_per_city):
            seed = hash((city["city"], i)) % (2**32)
            rng = np.random.default_rng(seed)
            features = _derive_geo_features(city, rng)
            features["annual_revenue_eur"] = _compute_revenue(features, rng)
            rows.append(features)
    return pd.DataFrame(rows)


def export_cities_catalog(output_path: Path) -> None:
    catalog = []
    for city in EUROPE_CITIES:
        features = _derive_geo_features(city, RNG)
        catalog.append({
            "id": f"{city['city'].lower().replace(' ', '-')}-{city['country'][:2].lower()}",
            "city": city["city"],
            "country": city["country"],
            "latitude": city["lat"],
            "longitude": city["lon"],
            "population": city["pop"],
            "gdp_per_capita": city["gdp"],
            "foot_traffic_index": features["foot_traffic_index"],
            "city_tier": city["tier"],
            "has_existing_store": city["city"] in {"Madrid", "Barcelona", "Paris", "Berlin", "Milan", "London", "Amsterdam"},
            "actual_revenue_eur": None,
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(catalog, indent=2))


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parents[1] / "data"
    df = generate_training_data()
    df.to_csv(data_dir / "store_training_data.csv", index=False)
    export_cities_catalog(data_dir / "europe_cities.json")
    print(f"Generated {len(df)} training samples and {len(EUROPE_CITIES)} city catalog entries.")
