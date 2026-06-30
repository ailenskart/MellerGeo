"""FastAPI application for Meller Geo Intelligence."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.ai_intelligence import (
    apply_verified_competitors,
    apply_verified_social,
    apply_verified_stores,
    build_chat_context,
    build_city_intelligence_bundle,
    build_verified_intelligence,
)
from app.google_maps import get_google_api_status
from app.chat_service import chat
from app.commercial_properties import search_commercial_properties
from app.catchment import analyze_city_catchments, analyze_city_streets
from app.data_generator import get_city_features
from app.meller_stores import BRAND, get_all_stores, get_stores_for_city
from app.predictor import RevenuePredictor
from app.schemas import (
    BatchPredictRequest,
    ChatRequest,
    ChatResponse,
    CityDetailAnalysis,
    CityIntelligenceBundle,
    CommercialPropertySearch,
    CatchmentArea,
    CityLocation,
    StreetLocation,
    CompetitorAnalysis,
    GeoParameters,
    ModelMetrics,
    RevenuePrediction,
    SeasonalityAnalysis,
    SocialIntelligenceReport,
    StoreLookupResult,
)
from app.seasonality import compute_monthly_revenue, get_market_insights

app = FastAPI(
    title="Meller Geo Intelligence",
    description="AI-powered store location intelligence for Meller eyewear expansion across Europe",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = RevenuePredictor()
_prediction_cache: dict[str, RevenuePrediction] = {}


def _get_city(city_id: str) -> dict:
    cities = predictor.load_cities()
    city = next((c for c in cities if c["id"] == city_id), None)
    if not city:
        raise HTTPException(404, f"City {city_id} not found")
    return city


def _predict_for_city(city: dict, store_size_sqm: float = 80) -> RevenuePrediction:
    cache_key = f"{city['id']}:{store_size_sqm}"
    if cache_key in _prediction_cache:
        return _prediction_cache[cache_key]

    features = get_city_features(city["city"], store_size_sqm)
    if not features:
        raise HTTPException(404, f"Features not found for {city['city']}")

    params = GeoParameters(**features)
    prediction = predictor.predict(params)
    _prediction_cache[cache_key] = prediction
    return prediction


@app.get("/api/brand")
def get_brand():
    return BRAND


@app.get("/api/stores")
def list_meller_stores(city: str | None = None):
    if city:
        return get_stores_for_city(city)
    return get_all_stores()


@app.get("/api/health")
def health():
    gstatus = get_google_api_status()
    return {
        "status": "ok",
        "model_loaded": predictor.pipeline is not None,
        "city_count": len(predictor.load_cities()),
        "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "google_maps_enabled": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
        "google_maps_live": gstatus.get("live", False),
        "google_api_error": gstatus.get("error"),
        "ai_verification_enabled": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/api/metrics", response_model=ModelMetrics)
def get_metrics():
    if predictor.metrics is None:
        raise HTTPException(503, "Model not trained yet")
    return predictor.metrics


@app.get("/api/cities", response_model=list[CityLocation])
def get_cities(
    country: str | None = None,
    tier: int | None = None,
    search: str | None = None,
    limit: int = Query(default=500, le=500),
):
    cities = predictor.load_cities()
    if country:
        cities = [c for c in cities if c["country"].lower() == country.lower()]
    if tier:
        cities = [c for c in cities if c["city_tier"] == tier]
    if search:
        q = search.lower()
        cities = [c for c in cities if q in c["city"].lower() or q in c["country"].lower()]
    return cities[:limit]


@app.post("/api/cities/batch-predict", response_model=list[CityLocation])
def batch_predict(request: BatchPredictRequest):
    cities = predictor.load_cities()
    if request.country:
        cities = [c for c in cities if c["country"].lower() == request.country.lower()]
    if request.city_tier:
        cities = [c for c in cities if c["city_tier"] == request.city_tier]

    results = []
    for city in cities:
        try:
            pred = _predict_for_city(city, request.store_size_sqm)
            enriched = {**city}
            enriched["predicted_revenue_eur"] = pred.predicted_annual_revenue_eur
            enriched["viability_score"] = pred.viability_score
            results.append(enriched)
        except HTTPException:
            results.append(city)
    return results


@app.post("/api/predict", response_model=RevenuePrediction)
def predict_revenue(params: GeoParameters):
    try:
        return predictor.predict(params)
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e


@app.get("/api/cities/{city_id}/predict", response_model=RevenuePrediction)
def predict_city(city_id: str, store_size_sqm: float = 80):
    city = _get_city(city_id)
    return _predict_for_city(city, store_size_sqm)


@app.get("/api/cities/{city_id}/detail", response_model=CityDetailAnalysis)
def get_city_detail(city_id: str, store_size_sqm: float = 80):
    city = _get_city(city_id)
    catchments = analyze_city_catchments(city, store_size_sqm, predictor)
    streets = analyze_city_streets(city, store_size_sqm, predictor)
    return CityDetailAnalysis(
        city=city["city"],
        country=city["country"],
        city_id=city_id,
        catchments=catchments,
        streets=streets,
        top_catchment=catchments[0] if catchments else None,
        top_street=streets[0] if streets else None,
    )


@app.get("/api/cities/{city_id}/catchments", response_model=list[CatchmentArea])
def get_city_catchments(city_id: str, store_size_sqm: float = 80):
    city = _get_city(city_id)
    return analyze_city_catchments(city, store_size_sqm, predictor)


@app.get("/api/cities/{city_id}/streets", response_model=list[StreetLocation])
def get_city_streets(
    city_id: str,
    store_size_sqm: float = 80,
    catchment_id: str | None = None,
):
    city = _get_city(city_id)
    return analyze_city_streets(city, store_size_sqm, predictor, catchment_id)


@app.get("/api/cities/{city_id}/properties", response_model=CommercialPropertySearch)
async def get_commercial_properties(
    city_id: str,
    store_size_sqm: float = 80,
    catchment_id: str | None = None,
    street_id: str | None = None,
):
    from app.catchment_data import get_catchment_by_id, get_street_by_id

    city = _get_city(city_id)
    features = get_city_features(city["city"], store_size_sqm)
    foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)

    lat, lon = city["latitude"], city["longitude"]
    street_name = None

    if street_id:
        street = get_street_by_id(street_id, city["city"], lat, lon, city["city_tier"])
        if street:
            lat, lon = street["lat"], street["lon"]
            street_name = street["name"]
            catchment_id = street.get("catchment_id")
            foot_traffic = street.get("foot_traffic", foot_traffic)

    if catchment_id:
        catchment = get_catchment_by_id(catchment_id, city["city"], lat, lon, city["city_tier"])
        if catchment:
            lat, lon = catchment["center"][0], catchment["center"][1]
            foot_traffic = catchment.get("foot_traffic", foot_traffic)
            tourist_index = catchment.get("tourist", tourist_index)

    result = await search_commercial_properties(
        city=city["city"],
        country=city["country"],
        latitude=city["latitude"],
        longitude=city["longitude"],
        city_tier=city["city_tier"],
        foot_traffic=foot_traffic,
        tourist_index=tourist_index,
        target_size_sqm=store_size_sqm,
        catchment_id=catchment_id,
        street_id=street_id,
        street_name=street_name,
        filter_lat=lat if catchment_id or street_id else None,
        filter_lon=lon if catchment_id or street_id else None,
    )
    return CommercialPropertySearch(**result)


@app.get("/api/brokers")
def list_commercial_brokers():
    from app.commercial_properties_data import COMMERCIAL_BROKERS
    return [{"id": k, **v} for k, v in COMMERCIAL_BROKERS.items()]


@app.get("/api/cities/{city_id}/intelligence", response_model=CityIntelligenceBundle)
async def get_city_intelligence(
    city_id: str,
    store_size_sqm: float = 80,
    catchment_id: str | None = None,
    street_id: str | None = None,
):
    from app.catchment_data import get_catchment_by_id, get_street_by_id

    city = _get_city(city_id)
    prediction = _predict_for_city(city, store_size_sqm)
    features = get_city_features(city["city"], store_size_sqm)
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)
    foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)

    lat, lon = city["latitude"], city["longitude"]
    area_name = None
    street_name = None

    if street_id:
        street = get_street_by_id(street_id, city["city"], lat, lon, city["city_tier"])
        if street:
            lat, lon = street["lat"], street["lon"]
            street_name = street["name"]
            catchment_id = street.get("catchment_id")
            foot_traffic = street.get("foot_traffic", foot_traffic)

    if catchment_id:
        catchment = get_catchment_by_id(catchment_id, city["city"], lat, lon, city["city_tier"])
        if catchment:
            lat, lon = catchment["center"][0], catchment["center"][1]
            area_name = catchment["name"]
            foot_traffic = catchment.get("foot_traffic", foot_traffic)
            tourist_index = catchment.get("tourist", tourist_index)

    monthly = compute_monthly_revenue(prediction.predicted_annual_revenue_eur, city["city"], tourist_index)
    seasonality = SeasonalityAnalysis(
        city=city["city"],
        annual_revenue_eur=prediction.predicted_annual_revenue_eur,
        monthly_revenue=monthly,
        market_insights=get_market_insights(city["city"], city["country"], tourist_index, city["gdp_per_capita"]),
    )

    bundle = await build_city_intelligence_bundle(
        city, store_size_sqm, prediction.model_dump(), seasonality.model_dump(),
        catchment_id=catchment_id, street_id=street_id,
        area_name=area_name or street_name, lat=lat, lon=lon,
        tourist_index=tourist_index, foot_traffic=foot_traffic,
    )

    return CityIntelligenceBundle(
        competitors=CompetitorAnalysis(**bundle["competitors"]),
        stores=StoreLookupResult(**bundle["stores"]),
        social=SocialIntelligenceReport(
            google=bundle["social"]["google"],
            instagram=bundle["social"]["instagram"],
            twitter=bundle["social"]["twitter"],
            **{k: v for k, v in bundle["social"].items() if k not in ("google", "instagram", "twitter")},
        ),
        seasonality=seasonality,
        google_status=bundle["google_status"],
    )


@app.get("/api/cities/{city_id}/competitors", response_model=CompetitorAnalysis)
async def get_competitors(city_id: str, store_size_sqm: float = 80):
    city = _get_city(city_id)
    prediction = _predict_for_city(city, store_size_sqm)
    features = get_city_features(city["city"])
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)
    foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)

    intel = await build_verified_intelligence(
        city, store_size_sqm, prediction.model_dump(),
        tourist_index=tourist_index, foot_traffic=foot_traffic,
    )
    result = apply_verified_competitors(intel["verified"], city)
    return CompetitorAnalysis(**result)


@app.get("/api/cities/{city_id}/seasonality", response_model=SeasonalityAnalysis)
def get_seasonality(city_id: str, store_size_sqm: float = 80):
    city = _get_city(city_id)
    prediction = _predict_for_city(city, store_size_sqm)
    features = get_city_features(city["city"], store_size_sqm)
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)

    monthly = compute_monthly_revenue(
        prediction.predicted_annual_revenue_eur,
        city["city"],
        tourist_index,
    )
    insights = get_market_insights(
        city["city"], city["country"], tourist_index, city["gdp_per_capita"]
    )

    return SeasonalityAnalysis(
        city=city["city"],
        annual_revenue_eur=prediction.predicted_annual_revenue_eur,
        monthly_revenue=monthly,
        market_insights=insights,
    )


@app.get("/api/cities/{city_id}/stores", response_model=StoreLookupResult)
async def lookup_stores(city_id: str, store_size_sqm: float = 80):
    import os
    city = _get_city(city_id)
    prediction = _predict_for_city(city, store_size_sqm)
    features = get_city_features(city["city"])
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)
    foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)

    intel = await build_verified_intelligence(
        city, store_size_sqm, prediction.model_dump(),
        tourist_index=tourist_index, foot_traffic=foot_traffic,
    )
    result = apply_verified_stores(intel, bool(os.getenv("GOOGLE_MAPS_API_KEY")))
    return StoreLookupResult(**result)


@app.get("/api/cities/{city_id}/social", response_model=SocialIntelligenceReport)
async def get_social_intelligence(
    city_id: str,
    catchment_id: str | None = None,
    street_id: str | None = None,
):
    from app.catchment_data import get_catchment_by_id, get_street_by_id

    city = _get_city(city_id)
    features = get_city_features(city["city"])
    tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)
    foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)

    lat, lon = city["latitude"], city["longitude"]
    area_name = None
    street_name = None

    if street_id:
        street = get_street_by_id(street_id, city["city"], lat, lon, city["city_tier"])
        if street:
            lat, lon = street["lat"], street["lon"]
            street_name = street["name"]
            catchment_id = street.get("catchment_id")
            foot_traffic = street.get("foot_traffic", foot_traffic)

    if catchment_id:
        catchment = get_catchment_by_id(catchment_id, city["city"], lat, lon, city["city_tier"])
        if catchment:
            lat, lon = catchment["center"][0], catchment["center"][1]
            area_name = catchment["name"]
            foot_traffic = catchment.get("foot_traffic", foot_traffic)
            tourist_index = catchment.get("tourist", tourist_index)

    prediction = _predict_for_city(city, 80)
    intel = await build_verified_intelligence(
        city, 80, prediction.model_dump(),
        catchment_id=catchment_id, street_id=street_id,
        area_name=area_name or street_name, lat=lat, lon=lon,
        tourist_index=tourist_index, foot_traffic=foot_traffic,
    )
    result = apply_verified_social(intel, city)

    return SocialIntelligenceReport(
        google=result["google"],
        instagram=result["instagram"],
        twitter=result["twitter"],
        **{k: v for k, v in result.items() if k not in ("google", "instagram", "twitter")},
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    context: dict = {}

    if request.city_id:
        city = _get_city(request.city_id)
        prediction = _predict_for_city(city, request.store_size_sqm)
        features = get_city_features(city["city"], request.store_size_sqm)
        tourist_index = features["tourist_index"] if features else city.get("tourist_index", 30)
        foot_traffic = features["foot_traffic_index"] if features else city.get("foot_traffic_index", 50)

        monthly = compute_monthly_revenue(
            prediction.predicted_annual_revenue_eur,
            city["city"], tourist_index,
        )
        market_insights = get_market_insights(
            city["city"], city["country"], tourist_index, city["gdp_per_capita"]
        )

        intel = await build_verified_intelligence(
            city, request.store_size_sqm, prediction.model_dump(),
            tourist_index=tourist_index, foot_traffic=foot_traffic,
        )
        context = build_chat_context(
            intel, city, prediction.model_dump(),
            {"monthly": monthly}, market_insights,
        )

    return await chat(request, context)


STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{path:path}")
    def serve_spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
