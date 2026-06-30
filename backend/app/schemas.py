from pydantic import BaseModel, Field


class GeoParameters(BaseModel):
    """Geographical and market parameters for a potential store location."""

    city: str = Field(..., description="City name")
    country: str = Field(..., description="ISO country name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    population: int = Field(..., ge=1000, description="City population")
    population_density: float = Field(..., ge=0, description="People per km²")
    gdp_per_capita: float = Field(..., ge=0, description="GDP per capita in EUR")
    avg_household_income: float = Field(..., ge=0, description="Annual household income EUR")
    foot_traffic_index: float = Field(..., ge=0, le=100, description="Pedestrian traffic score 0-100")
    tourist_index: float = Field(..., ge=0, le=100, description="Tourist footfall score 0-100")
    fashion_competitor_density: float = Field(..., ge=0, description="Fashion retailers per 10k residents")
    luxury_retail_proximity: float = Field(..., ge=0, le=100, description="Nearby luxury retail score")
    public_transport_score: float = Field(..., ge=0, le=100)
    retail_rent_index: float = Field(..., ge=0, le=100, description="Relative rent cost 0-100")
    median_age: float = Field(..., ge=15, le=80)
    ecommerce_penetration: float = Field(..., ge=0, le=100, description="% online eyewear purchases")
    mall_vs_street: float = Field(..., ge=0, le=1, description="0=street, 1=mall location")
    store_size_sqm: float = Field(default=80, ge=20, le=500)
    city_tier: int = Field(..., ge=1, le=3, description="1=capital/major, 2=secondary, 3=smaller")


class RevenuePrediction(BaseModel):
    predicted_annual_revenue_eur: float
    confidence_interval_low: float
    confidence_interval_high: float
    revenue_per_sqm: float
    viability_score: float = Field(..., ge=0, le=100)
    viability_label: str
    key_drivers: list[dict[str, float | str]]
    recommendation: str


class CityLocation(BaseModel):
    id: str
    city: str
    country: str
    latitude: float
    longitude: float
    population: int
    gdp_per_capita: float
    foot_traffic_index: float
    city_tier: int
    has_existing_store: bool = False
    actual_revenue_eur: float | None = None


class ModelMetrics(BaseModel):
    r2_score: float
    mae_eur: float
    rmse_eur: float
    training_samples: int
    feature_importance: list[dict[str, float | str]]
