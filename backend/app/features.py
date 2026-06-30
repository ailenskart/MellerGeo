"""Feature engineering for Meller store revenue prediction."""

FEATURE_COLUMNS = [
    "population",
    "population_density",
    "gdp_per_capita",
    "avg_household_income",
    "foot_traffic_index",
    "tourist_index",
    "fashion_competitor_density",
    "luxury_retail_proximity",
    "public_transport_score",
    "retail_rent_index",
    "median_age",
    "ecommerce_penetration",
    "mall_vs_street",
    "store_size_sqm",
    "city_tier",
]

FEATURE_LABELS = {
    "population": "Population",
    "population_density": "Population Density",
    "gdp_per_capita": "GDP per Capita",
    "avg_household_income": "Household Income",
    "foot_traffic_index": "Foot Traffic",
    "tourist_index": "Tourist Index",
    "fashion_competitor_density": "Competitor Density",
    "luxury_retail_proximity": "Luxury Retail Proximity",
    "public_transport_score": "Public Transport",
    "retail_rent_index": "Retail Rent",
    "median_age": "Median Age",
    "ecommerce_penetration": "E-commerce Penetration",
    "mall_vs_street": "Mall vs Street",
    "store_size_sqm": "Store Size",
    "city_tier": "City Tier",
}


def params_to_vector(params: dict) -> list[float]:
    return [float(params[col]) for col in FEATURE_COLUMNS]
