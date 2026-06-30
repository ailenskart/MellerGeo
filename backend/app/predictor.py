"""ML predictor for Meller store revenue."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.features import FEATURE_COLUMNS, FEATURE_LABELS, params_to_vector
from app.schemas import GeoParameters, ModelMetrics, RevenuePrediction

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "revenue_model.joblib"
METRICS_PATH = Path(__file__).resolve().parents[1] / "models" / "metrics.json"
CITIES_PATH = Path(__file__).resolve().parents[1] / "data" / "europe_cities.json"


class RevenuePredictor:
    def __init__(self) -> None:
        self.pipeline: Pipeline | None = None
        self.metrics: ModelMetrics | None = None
        self._load()

    def _load(self) -> None:
        if MODEL_PATH.exists():
            self.pipeline = joblib.load(MODEL_PATH)
        if METRICS_PATH.exists():
            data = json.loads(METRICS_PATH.read_text())
            self.metrics = ModelMetrics(**data)

    def train(self, df: pd.DataFrame) -> ModelMetrics:
        X = df[FEATURE_COLUMNS].values
        y = df["annual_revenue_eur"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.08,
                subsample=0.85,
                random_state=42,
            )),
        ])
        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        r2 = float(r2_score(y_test, y_pred))
        mae = float(mean_absolute_error(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

        cv_scores = cross_val_score(
            self.pipeline, X, y, cv=5, scoring="r2"
        )

        model = self.pipeline.named_steps["model"]
        importances = model.feature_importances_
        feature_importance = [
            {"feature": FEATURE_LABELS[col], "importance": round(float(imp), 4)}
            for col, imp in sorted(
                zip(FEATURE_COLUMNS, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        ]

        self.metrics = ModelMetrics(
            r2_score=round(r2, 4),
            mae_eur=round(mae, 0),
            rmse_eur=round(rmse, 0),
            training_samples=len(df),
            feature_importance=feature_importance,
        )

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, MODEL_PATH)
        METRICS_PATH.write_text(self.metrics.model_dump_json(indent=2))

        return self.metrics

    def predict(self, params: GeoParameters) -> RevenuePrediction:
        if self.pipeline is None:
            raise RuntimeError("Model not trained. Run train_model.py first.")

        vector = np.array([params_to_vector(params.model_dump())])
        prediction = float(self.pipeline.predict(vector)[0])

        # Estimate uncertainty from model residuals (approximation)
        mae = self.metrics.mae_eur if self.metrics else prediction * 0.12
        ci_low = max(0, prediction - mae * 1.2)
        ci_high = prediction + mae * 1.2
        revenue_per_sqm = prediction / params.store_size_sqm

        viability = self._compute_viability(params, prediction, revenue_per_sqm)
        drivers = self._top_drivers(params)
        recommendation = self._recommendation(viability, prediction, params)

        return RevenuePrediction(
            predicted_annual_revenue_eur=round(prediction, 0),
            confidence_interval_low=round(ci_low, 0),
            confidence_interval_high=round(ci_high, 0),
            revenue_per_sqm=round(revenue_per_sqm, 0),
            viability_score=viability["score"],
            viability_label=viability["label"],
            key_drivers=drivers,
            recommendation=recommendation,
        )

    def _compute_viability(
        self, params: GeoParameters, revenue: float, revenue_per_sqm: float
    ) -> dict:
        score = 0.0

        # Revenue benchmarks for Meller stores
        if revenue >= 450_000:
            score += 35
        elif revenue >= 350_000:
            score += 28
        elif revenue >= 250_000:
            score += 20
        elif revenue >= 180_000:
            score += 12
        else:
            score += 5

        if revenue_per_sqm >= 4500:
            score += 25
        elif revenue_per_sqm >= 3500:
            score += 18
        elif revenue_per_sqm >= 2500:
            score += 10

        if params.foot_traffic_index >= 70:
            score += 15
        elif params.foot_traffic_index >= 50:
            score += 10
        elif params.foot_traffic_index >= 30:
            score += 5

        if params.gdp_per_capita >= 40_000:
            score += 10
        elif params.gdp_per_capita >= 28_000:
            score += 6

        rent_efficiency = revenue / max(params.retail_rent_index, 1)
        if rent_efficiency >= 6000:
            score += 15
        elif rent_efficiency >= 4000:
            score += 8

        score = min(100, score)
        if score >= 75:
            label = "Highly Recommended"
        elif score >= 55:
            label = "Recommended"
        elif score >= 35:
            label = "Moderate Potential"
        else:
            label = "Not Recommended"

        return {"score": round(score, 1), "label": label}

    def _top_drivers(self, params: GeoParameters) -> list[dict]:
        if not self.metrics:
            return []

        importance_map = {
            item["feature"]: item["importance"]
            for item in self.metrics.feature_importance
        }
        values = {
            FEATURE_LABELS[col]: getattr(params, col)
            for col in FEATURE_COLUMNS
        }
        drivers = []
        for label, importance in sorted(
            importance_map.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            drivers.append({
                "factor": label,
                "importance": importance,
                "value": values.get(label, "N/A"),
            })
        return drivers

    def _recommendation(
        self, viability: dict, revenue: float, params: GeoParameters
    ) -> str:
        city = params.city
        if viability["score"] >= 75:
            return (
                f"Strong candidate for a Meller store in {city}. "
                f"Projected annual revenue of €{revenue:,.0f} with excellent "
                f"foot traffic and purchasing power alignment."
            )
        if viability["score"] >= 55:
            return (
                f"{city} shows solid potential. Consider a {int(params.store_size_sqm)}m² "
                f"{'mall' if params.mall_vs_street > 0.5 else 'street'} location. "
                f"Expected revenue: €{revenue:,.0f}/year."
            )
        if viability["score"] >= 35:
            return (
                f"Moderate opportunity in {city}. Revenue projection of €{revenue:,.0f} "
                f"may justify a smaller format store or pop-up to test the market."
            )
        return (
            f"Limited viability in {city} based on current parameters. "
            f"Consider alternative locations or wait for market conditions to improve."
        )

    def load_cities(self) -> list[dict]:
        if CITIES_PATH.exists():
            return json.loads(CITIES_PATH.read_text())
        return []
