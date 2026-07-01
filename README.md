# MELLER Geo Intelligence

Internal expansion intelligence platform for **[MELLER](https://mellerbrand.com/)** — the Barcelona-born sunglasses and eyewear brand trusted by 3M+ customers.

Built to help MELLER plan **MELLER Factory** store openings across Europe, learning from geographical parameters to predict average annual revenue.

![MELLER](https://img.shields.io/badge/MELLER-Geo%20Intelligence-FF6723)

## Official MELLER Stores

Per [mellerbrand.com/pages/our-stores](https://mellerbrand.com/pages/our-stores):

| City | Address | Concept |
|------|---------|---------|
| Barcelona | Calle Portaferrissa 18 | MELLER Factory flagship |
| Barcelona | Carrer de l'Argenteria 63 | MELLER Factory — Born |
| Amsterdam | 160 Kalverstraat | MELLER Factory + photo booth |
| Paris | 19 Rue des Rosiers | MELLER Factory — Le Marais |

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
- **Catchment & Street Analysis** — Drill into any city to compare districts and specific retail streets
- **Social Intelligence** — Google reviews, Instagram buzz, and X/Twitter shopping signals with sentiment analysis

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React Frontend │────▶│  FastAPI Backend │────▶│  ML Model (sklearn) │
│  Leaflet Map    │     │  /api/predict    │     │  Gradient Boosting  │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

## Hosting

### Deploy to Vercel (recommended — permanent URL)

**Your permanent link after deploy:** `https://meller-geo-intelligence.vercel.app`

1. Go to [vercel.com/new](https://vercel.com/new) and sign in with GitHub
2. Import the **MellerGeo** repository
3. Vercel auto-detects settings from `vercel.json` — click **Deploy**
4. After deploy, open **Settings → Environment Variables** and add:
   - `GOOGLE_MAPS_API_KEY` — live Maps, competitors, Street View
   - `OPENAI_API_KEY` — AI chat and verification (optional)
5. Redeploy from the Deployments tab

Every push to `main` auto-redeploys. Free tier API routes have a 10s timeout; Pro ($20/mo) allows 60s for heavy intelligence calls.

### Production (local single server)

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

### Deploy to Render (permanent URL)

**Your permanent link after deploy:** `https://meller-geo-intelligence.onrender.com`

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ailenskart/MellerGeo)

1. Click **Deploy to Render** above (or open [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → connect `MellerGeo`)
2. When prompted, set environment variables:
   - `GOOGLE_MAPS_API_KEY` — your Google Maps demo/production key
   - `OPENAI_API_KEY` — for AI chat and verification (optional)
3. Click **Apply** — first deploy takes ~5–8 minutes
4. Open **https://meller-geo-intelligence.onrender.com**

The service auto-redeploys on every push to `main`. Free tier may sleep after 15 min idle (first load ~30s).

> **Note:** Cloudflare `trycloudflare.com` links are temporary dev tunnels only — they change every restart. Use Render for a stable URL.

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
