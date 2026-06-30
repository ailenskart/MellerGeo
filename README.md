# Meller Geo Intelligence

AI-powered geographical intelligence platform for **Meller** eyewear store expansion across Europe. The tool learns from 15+ geographical and market parameters to predict average annual revenue for potential store locations.

![Meller Geo Intelligence](https://img.shields.io/badge/Meller-Geo%20Intelligence-c8a96e)

## Features

- **176+ European Cities** — Comprehensive coverage across 30+ countries
- **Interactive Europe Map** — Color-coded viability markers with search and tier filters
- **ML Revenue Prediction** — Gradient Boosting model trained on 15 geo parameters (85% accuracy)
- **AI Chat Advisor** — LLM-powered assistant for revenue, competitors, seasonality, and expansion strategy
- **Competitor Analysis** — Ray-Ban, Oakley, Persol, Gentle Monster, Hawkers, and 15+ sunglasses brands
- **Seasonal Revenue Forecasting** — Monthly breakdown with tourist season and peak period analysis
- **Google Maps Integration** — Live Meller store lookup, competitor POIs, and estimated store sizes
- **15 Geo Parameters** — Population, GDP, foot traffic, tourism, competitor density, and more
- **Viability Scoring** — 0–100 score with actionable recommendations
- **Store Size Simulator** — Adjust store size (40–200 m²) and see revenue impact in real time

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  ML Model (sklearn) │
│  Leaflet Map    │     │  /api/predict    │     │  Gradient Boosting  │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

## Hosting

### Production (single server)

The backend serves both the API and the built React frontend:

```bash
./scripts/start-production.sh
```

Open http://localhost:8000

### Docker

```bash
docker build -t meller-geo .
docker run -p 8000:8000 meller-geo
```

### Deploy to Render (permanent, free tier)

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect the `MellerGeo` repository and deploy
4. Set environment variables in Render:
   - `OPENAI_API_KEY` — enables full LLM chat (optional, falls back to local advisor)
   - `GOOGLE_MAPS_API_KEY` — enables live store/competitor lookup via Google Places (optional)

The included `render.yaml` configures a Docker web service in the Frankfurt region with health checks on `/api/health`.

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/cities` | List all European cities |
| GET | `/api/metrics` | Model performance metrics |
| GET | `/api/cities/{id}/predict` | Predict revenue for a city |
| POST | `/api/predict` | Predict revenue with custom parameters |

### Example Prediction Request

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Milan",
    "country": "Italy",
    "latitude": 45.4642,
    "longitude": 9.1900,
    "population": 1350000,
    "population_density": 7500,
    "gdp_per_capita": 41600,
    "avg_household_income": 38000,
    "foot_traffic_index": 78,
    "tourist_index": 65,
    "fashion_competitor_density": 3.2,
    "luxury_retail_proximity": 82,
    "public_transport_score": 75,
    "retail_rent_index": 68,
    "median_age": 39,
    "ecommerce_penetration": 32,
    "mall_vs_street": 0.3,
    "store_size_sqm": 80,
    "city_tier": 1
  }'
```

## Geographical Parameters

The model learns from these parameters to predict store revenue:

| Parameter | Description |
|-----------|-------------|
| Population | City population |
| Population Density | People per km² |
| GDP per Capita | Economic purchasing power |
| Household Income | Average annual household income |
| Foot Traffic Index | Pedestrian traffic score (0–100) |
| Tourist Index | Tourist footfall score (0–100) |
| Competitor Density | Fashion retailers per 10k residents |
| Luxury Retail Proximity | Nearby luxury retail score |
| Public Transport Score | Transit accessibility (0–100) |
| Retail Rent Index | Relative rent cost (0–100) |
| Median Age | City median age |
| E-commerce Penetration | Online eyewear purchase rate |
| Mall vs Street | Location type (0=street, 1=mall) |
| Store Size | Square meters |
| City Tier | 1=major, 2=secondary, 3=smaller |

## Training Your Own Model

Replace the synthetic training data with real Meller store performance data:

1. Export store data to `backend/data/store_training_data.csv`
2. Ensure columns match `FEATURE_COLUMNS` in `app/features.py` plus `annual_revenue_eur`
3. Run `python train_model.py`

The model will retrain and save to `backend/models/revenue_model.joblib`.

## Tech Stack

- **Backend**: Python, FastAPI, scikit-learn, pandas
- **Frontend**: React, TypeScript, Vite, Leaflet, Recharts
- **ML**: Gradient Boosting Regressor with StandardScaler pipeline

## License

Proprietary — Meller Internal Use
