from pydantic import BaseModel, Field


class GeoParameters(BaseModel):
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
    tourist_index: float = 0
    city_tier: int
    has_existing_store: bool = False
    actual_revenue_eur: float | None = None
    predicted_revenue_eur: float | None = None
    viability_score: float | None = None


class ModelMetrics(BaseModel):
    r2_score: float
    mae_eur: float
    rmse_eur: float
    training_samples: int
    feature_importance: list[dict[str, float | str]]


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    city_id: str | None = None
    store_size_sqm: float = 80


class ChatResponse(BaseModel):
    message: ChatMessage
    context_used: list[str]
    source: str


class CompetitorStore(BaseModel):
    brand: str
    tier: str
    latitude: float
    longitude: float
    distance_km: float
    rating: float
    estimated_annual_revenue_eur: float
    store_type: str


class CompetitorAnalysis(BaseModel):
    city: str
    country: str
    total_competitors: int
    brands_present: list[str]
    market_saturation_score: float
    luxury_competitor_count: int
    direct_eyewear_stores: int
    nearest_competitors: list[CompetitorStore]
    market_assessment: str
    meller_opportunity_score: float


class MonthlyRevenue(BaseModel):
    month: int
    month_name: str
    revenue_eur: float
    seasonal_index: float
    season: str


class SeasonalityAnalysis(BaseModel):
    city: str
    annual_revenue_eur: float
    monthly_revenue: list[MonthlyRevenue]
    market_insights: dict


class PlaceResult(BaseModel):
    place_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    rating: float | None = None
    user_ratings_total: int = 0
    business_status: str = "OPERATIONAL"
    types: list[str] = []
    estimated_size_sqm: int = 80


class StoreLookupResult(BaseModel):
    meller_stores: list[PlaceResult]
    nearby_competitors: list[PlaceResult]
    google_maps_enabled: bool


class BatchPredictRequest(BaseModel):
    store_size_sqm: float = 80
    city_tier: int | None = None
    country: str | None = None


class SocialReview(BaseModel):
    author: str
    rating: float | None = None
    text: str
    time: str
    source: str
    likes: int | None = None
    comments: int | None = None
    sentiment: str | None = None


class ShoppingDestination(BaseModel):
    name: str
    social_buzz_score: float
    google_rating: float
    foot_traffic_estimate: float
    instagram_mentions: int
    why_popular: str
    best_for: str


class PlatformSocialData(BaseModel):
    platform: str
    sentiment_score: float
    mention_volume_monthly: int | None = None
    average_rating: float | None = None
    total_reviews: int | None = None
    review_count_analyzed: int | None = None
    engagement_rate: float | None = None
    top_posts: list[dict] = []
    top_rated_nearby: list[dict] = []
    reviews: list[SocialReview] = []
    hashtag_volume: dict[str, int] = {}
    trending_topics: list[str] = []
    shopping_tags: list[str] = []
    influencer_visits_monthly: int | None = None
    shopping_intent_mentions: int | None = None


class SocialIntelligenceReport(BaseModel):
    location: str
    city: str
    country: str
    latitude: float
    longitude: float
    overall_sentiment_score: float
    overall_sentiment_label: str
    shopping_intent_score: float
    google: PlatformSocialData
    instagram: PlatformSocialData
    twitter: PlatformSocialData
    shopping_destinations: list[ShoppingDestination]
    top_positive_themes: list[str]
    top_negative_themes: list[str]
    where_people_shop: list[str]
    data_sources: dict[str, bool]
    summary: str


class CatchmentArea(BaseModel):
    id: str
    name: str
    type: str
    type_label: str
    center: dict[str, float]
    polygon: list[list[float]]
    foot_traffic_index: float
    tourist_index: float
    luxury_retail_score: float
    retail_rent_index: float
    has_meller_store: bool = False
    predicted_annual_revenue_eur: float
    viability_score: float
    viability_label: str
    revenue_per_sqm: float
    recommendation: str
    street_count: int = 0


class StreetLocation(BaseModel):
    id: str
    name: str
    catchment_id: str | None = None
    catchment_name: str | None = None
    type: str
    type_label: str
    latitude: float
    longitude: float
    foot_traffic_index: float
    retail_rent_index: float
    street_width_m: float | None = None
    has_meller_store: bool = False
    predicted_annual_revenue_eur: float
    viability_score: float
    viability_label: str
    revenue_per_sqm: float
    confidence_interval_low: float | None = None
    confidence_interval_high: float | None = None
    recommendation: str
    key_drivers: list[dict[str, float | str]] = []


class CityDetailAnalysis(BaseModel):
    city: str
    country: str
    city_id: str
    catchments: list[CatchmentArea]
    streets: list[StreetLocation]
    top_catchment: CatchmentArea | None = None
    top_street: StreetLocation | None = None
