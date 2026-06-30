"""Generate realistic synthetic training data for Meller European stores."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.cities_catalog import EUROPE_CITIES, _city_id, has_meller_store, is_tourist_city
from app.features import FEATURE_COLUMNS

RNG = np.random.default_rng(42)


def _stable_rng(city: str, salt: str = "") -> np.random.Generator:
    h = hashlib.md5(f"{city}:{salt}".encode()).hexdigest()
    return np.random.default_rng(int(h[:8], 16))


def _derive_geo_features(city: dict, rng: np.random.Generator | None = None) -> dict:
    if rng is None:
        rng = _stable_rng(city["city"], "features")

    tier = city["tier"]
    pop = city["pop"]
    gdp = city["gdp"]

    density = pop / rng.uniform(80, 450)
    income = gdp * rng.uniform(0.65, 0.95)
    foot_traffic = min(100, 35 + tier * 15 + rng.normal(0, 8) + (gdp / 1000))
    tourist = min(100, rng.uniform(40, 90) if is_tourist_city(city["city"]) else rng.uniform(5, 45))
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


def get_city_features(city_name: str, store_size_sqm: float = 80) -> dict | None:
    city_data = next((c for c in EUROPE_CITIES if c["city"] == city_name), None)
    if not city_data:
        return None
    features = _derive_geo_features(city_data)
    features["store_size_sqm"] = store_size_sqm
    return features


def _compute_revenue(row: dict, rng: np.random.Generator) -> float:
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
        base * income_factor * traffic_factor * tourist_factor * luxury_factor
        * transport_factor * size_factor * tier_factor * competitor_penalty
        * rent_penalty * ecommerce_penalty * mall_bonus * age_factor
    )
    return round(revenue * rng.lognormal(0, 0.08), 0)


def generate_training_data(n_per_city: int = 4) -> pd.DataFrame:
    rows = []
    for city in EUROPE_CITIES:
        for i in range(n_per_city):
            rng = _stable_rng(city["city"], f"train_{i}")
            features = _derive_geo_features(city, rng)
            features["annual_revenue_eur"] = _compute_revenue(features, rng)
            rows.append(features)
    return pd.DataFrame(rows)


def export_cities_catalog(output_path: Path) -> None:
    catalog = []
    for city in EUROPE_CITIES:
        features = _derive_geo_features(city)
        catalog.append({
            "id": _city_id(city["city"], city["country"]),
            "city": city["city"],
            "country": city["country"],
            "latitude": city["lat"],
            "longitude": city["lon"],
            "population": city["pop"],
            "gdp_per_capita": city["gdp"],
            "foot_traffic_index": features["foot_traffic_index"],
            "tourist_index": features["tourist_index"],
            "city_tier": city["tier"],
            "has_existing_store": has_meller_store(city["city"]),
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
