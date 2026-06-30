"""Seasonal revenue modeling for European retail locations."""

from __future__ import annotations

from app.cities_catalog import is_tourist_city

# Monthly indices (1.0 = average month) by city profile
BASE_SEASONAL = [0.85, 0.82, 0.90, 0.95, 1.05, 1.15, 1.20, 1.18, 1.05, 0.95, 1.10, 1.25]

TOURIST_SEASONAL = [0.70, 0.72, 0.85, 0.95, 1.10, 1.30, 1.45, 1.40, 1.15, 0.90, 0.80, 0.95]

SKI_SEASONAL = [1.30, 1.25, 1.10, 0.85, 0.75, 0.70, 0.72, 0.78, 0.85, 0.95, 1.15, 1.40]

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SKI_CITIES = {"St. Moritz", "Innsbruck", "Salzburg"}


def get_seasonal_profile(city: str, tourist_index: float) -> list[float]:
    if city in SKI_CITIES:
        return SKI_SEASONAL
    if is_tourist_city(city) or tourist_index >= 60:
        return TOURIST_SEASONAL
    return BASE_SEASONAL


def compute_monthly_revenue(
    annual_revenue: float,
    city: str,
    tourist_index: float,
) -> list[dict]:
    profile = get_seasonal_profile(city, tourist_index)
    total = sum(profile)
    normalized = [p / total * 12 for p in profile]

    months = []
    for i, factor in enumerate(normalized):
        monthly = annual_revenue / 12 * factor
        months.append({
            "month": i + 1,
            "month_name": MONTH_NAMES[i],
            "revenue_eur": round(monthly, 0),
            "seasonal_index": round(factor, 3),
            "season": _season_label(i + 1),
        })
    return months


def _season_label(month: int) -> str:
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


def get_market_insights(city: str, country: str, tourist_index: float, gdp: float) -> dict:
    profile = get_seasonal_profile(city, tourist_index)
    peak_month = MONTH_NAMES[profile.index(max(profile))]
    low_month = MONTH_NAMES[profile.index(min(profile))]
    peak_factor = max(profile)
    low_factor = min(profile)

    is_tourist = is_tourist_city(city) or tourist_index >= 60

    insights = {
        "peak_season": peak_month,
        "low_season": low_month,
        "peak_vs_low_ratio": round(peak_factor / low_factor, 2),
        "is_tourist_destination": is_tourist,
        "tourist_index": tourist_index,
        "recommended_opening_month": "March" if is_tourist else "September",
        "holiday_boost": "December (+25% gifting season)" if gdp > 35000 else "November-December",
        "summer_revenue_share": round(sum(profile[5:8]) / sum(profile) * 100, 1),
    }
    return insights
