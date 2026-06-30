"""FastAPI application for Meller Geo Intelligence."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.predictor import RevenuePredictor
from app.schemas import CityLocation, GeoParameters, ModelMetrics, RevenuePrediction

app = FastAPI(
    title="Meller Geo Intelligence",
    description="AI-powered store location intelligence for Meller eyewear expansion across Europe",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = RevenuePredictor()

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_loaded": predictor.pipeline is not None,
    }


@app.get("/api/metrics", response_model=ModelMetrics)
def get_metrics():
    if predictor.metrics is None:
        raise HTTPException(503, "Model not trained yet")
    return predictor.metrics


@app.get("/api/cities", response_model=list[CityLocation])
def get_cities():
    return predictor.load_cities()


@app.post("/api/predict", response_model=RevenuePrediction)
def predict_revenue(params: GeoParameters):
    try:
        return predictor.predict(params)
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e


@app.get("/api/cities/{city_id}/predict", response_model=RevenuePrediction)
def predict_city(city_id: str, store_size_sqm: float = 80):
    cities = predictor.load_cities()
    city = next((c for c in cities if c["id"] == city_id), None)
    if not city:
        raise HTTPException(404, f"City {city_id} not found")

    from app.data_generator import _derive_geo_features
    import numpy as np

    city_data = next(
        c for c in __import__("app.data_generator", fromlist=["EUROPE_CITIES"]).EUROPE_CITIES
        if c["city"] == city["city"]
    )
    features = _derive_geo_features(city_data, np.random.default_rng(0))
    features["store_size_sqm"] = store_size_sqm

    params = GeoParameters(**features)
    return predictor.predict(params)


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
