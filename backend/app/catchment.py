"""Catchment and street-level revenue analysis."""

from __future__ import annotations

from app.catchment_data import (
    CATCHMENT_TYPE_LABELS,
    STREET_TYPE_LABELS,
    get_catchment_by_id,
    get_catchments,
    get_street_by_id,
    get_streets,
)
from app.data_generator import get_city_features
from app.predictor import RevenuePredictor
from app.schemas import GeoParameters, RevenuePrediction


def analyze_city_catchments(
    city: dict,
    store_size_sqm: float,
    predictor: RevenuePredictor,
) -> list[dict]:
    catchments = get_catchments(
        city["city"], city["latitude"], city["longitude"], city["city_tier"]
    )
    base_features = get_city_features(city["city"], store_size_sqm)
    if not base_features:
        return []

    results = []
    for catchment in catchments:
        prediction = _predict_for_location(
            city, base_features, catchment, store_size_sqm, predictor, level="catchment"
        )
        results.append({
            "id": catchment["id"],
            "name": catchment["name"],
            "type": catchment["type"],
            "type_label": CATCHMENT_TYPE_LABELS.get(catchment["type"], catchment["type"]),
            "center": {"latitude": catchment["center"][0], "longitude": catchment["center"][1]},
            "polygon": [[p[0], p[1]] for p in catchment["polygon"]],
            "foot_traffic_index": catchment["foot_traffic"],
            "tourist_index": catchment["tourist"],
            "luxury_retail_score": catchment["luxury"],
            "retail_rent_index": catchment["rent"],
            "has_meller_store": catchment.get("has_meller_store", False),
            "predicted_annual_revenue_eur": prediction.predicted_annual_revenue_eur,
            "viability_score": prediction.viability_score,
            "viability_label": prediction.viability_label,
            "revenue_per_sqm": prediction.revenue_per_sqm,
            "recommendation": prediction.recommendation,
            "street_count": len([s for s in get_streets(city["city"], city["latitude"], city["longitude"], city["city_tier"]) if s.get("catchment_id") == catchment["id"]]),
        })

    results.sort(key=lambda x: x["viability_score"], reverse=True)
    return results


def analyze_city_streets(
    city: dict,
    store_size_sqm: float,
    predictor: RevenuePredictor,
    catchment_id: str | None = None,
) -> list[dict]:
    streets = get_streets(city["city"], city["latitude"], city["longitude"], city["city_tier"])
    if catchment_id:
        streets = [s for s in streets if s.get("catchment_id") == catchment_id]

    base_features = get_city_features(city["city"], store_size_sqm)
    if not base_features:
        return []

    catchment_map = {c["id"]: c for c in get_catchments(city["city"], city["latitude"], city["longitude"], city["city_tier"])}

    results = []
    for street in streets:
        catchment = catchment_map.get(street.get("catchment_id", ""), {})
        location = {
            "foot_traffic": street["foot_traffic"],
            "tourist": catchment.get("tourist", base_features["tourist_index"]),
            "luxury": catchment.get("luxury", base_features["luxury_retail_proximity"]),
            "rent": street["rent_index"],
            "income_factor": catchment.get("income_factor", 1.0),
            "center": [street["lat"], street["lon"]],
        }
        prediction = _predict_for_location(
            city, base_features, location, store_size_sqm, predictor, level="street"
        )
        results.append({
            "id": street["id"],
            "name": street["name"],
            "catchment_id": street.get("catchment_id"),
            "catchment_name": catchment.get("name"),
            "type": street["type"],
            "type_label": STREET_TYPE_LABELS.get(street["type"], street["type"]),
            "latitude": street["lat"],
            "longitude": street["lon"],
            "foot_traffic_index": street["foot_traffic"],
            "retail_rent_index": street["rent_index"],
            "street_width_m": street.get("width_m"),
            "has_meller_store": street.get("has_meller", False),
            "predicted_annual_revenue_eur": prediction.predicted_annual_revenue_eur,
            "viability_score": prediction.viability_score,
            "viability_label": prediction.viability_label,
            "revenue_per_sqm": prediction.revenue_per_sqm,
            "confidence_interval_low": prediction.confidence_interval_low,
            "confidence_interval_high": prediction.confidence_interval_high,
            "recommendation": _street_recommendation(street, prediction, catchment),
            "key_drivers": prediction.key_drivers,
        })

    results.sort(key=lambda x: x["viability_score"], reverse=True)
    return results


def _predict_for_location(
    city: dict,
    base_features: dict,
    location: dict,
    store_size_sqm: float,
    predictor: RevenuePredictor,
    level: str,
) -> RevenuePrediction:
    features = {**base_features}
    features["foot_traffic_index"] = location.get("foot_traffic", base_features["foot_traffic_index"])
    features["tourist_index"] = location.get("tourist", base_features["tourist_index"])
    features["luxury_retail_proximity"] = location.get("luxury", base_features["luxury_retail_proximity"])
    features["retail_rent_index"] = location.get("rent", base_features["retail_rent_index"])
    features["avg_household_income"] = base_features["avg_household_income"] * location.get("income_factor", 1.0)
    features["store_size_sqm"] = store_size_sqm

    center = location.get("center", [city["latitude"], city["longitude"]])
    features["latitude"] = center[0]
    features["longitude"] = center[1]

    if level == "street":
        features["mall_vs_street"] = 0.0

    params = GeoParameters(**features)
    return predictor.predict(params)


def _street_recommendation(street: dict, prediction: RevenuePrediction, catchment: dict) -> str:
    name = street["name"]
    if street.get("has_meller"):
        return f"Existing MELLER store on {name}. Benchmark for new locations in {catchment.get('name', 'this area')}."
    score = prediction.viability_score
    if score >= 75:
        return f"Prime location — {name} offers excellent foot traffic and strong revenue potential for a MELLER Factory store."
    if score >= 55:
        return f"Solid option on {name}. Consider 80–100m² street-level format with high-visibility storefront."
    if score >= 35:
        return f"Moderate potential on {name}. Test with a smaller pop-up before committing to a full MELLER Factory."
    return f"Lower priority — {name} may not justify full retail investment. Explore other streets in {catchment.get('name', 'the area')}."
