"""LLM-powered chat assistant for Meller Geo Intelligence."""

from __future__ import annotations

import json
import os
from typing import Any

from app.schemas import ChatMessage, ChatRequest, ChatResponse

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are Meller Geo Intelligence AI — an expert retail expansion advisor for Meller, 
a European sunglasses and eyewear brand. You help analyze store locations across Europe.

You have access to:
- ML-predicted annual revenue for store locations
- 200+ European cities with geo/market data
- Competitor analysis (Ray-Ban, Oakley, Persol, Gentle Monster, Hawkers, etc.)
- Seasonal revenue patterns (tourist seasons, summer peaks, holiday gifting)
- Google Maps store data (when available)
- Viability scores and market saturation metrics

Guidelines:
- Be specific with numbers when context data is provided
- Compare cities and recommend optimal expansion strategy
- Consider seasonality, tourism, competitor density, and purchasing power
- For existing Meller stores, suggest optimization (size, location, seasonal staffing)
- Mention relevant sunglasses competitors in each market
- Use EUR for all revenue figures
- Be concise but insightful — you're advising retail executives
"""


async def chat(request: ChatRequest, context: dict[str, Any]) -> ChatResponse:
    messages = _build_messages(request, context)

    if OPENAI_API_KEY:
        reply = await _call_openai(messages)
        source = "openai"
    else:
        reply = _fallback_response(request.messages[-1].content, context)
        source = "local"

    return ChatResponse(
        message=ChatMessage(role="assistant", content=reply),
        context_used=_summarize_context(context),
        source=source,
    )


def _build_messages(request: ChatRequest, context: dict[str, Any]) -> list[dict]:
    context_block = f"\n\n--- Current Analysis Context ---\n{json.dumps(context, indent=2, default=str)}"

    msgs = [{"role": "system", "content": SYSTEM_PROMPT + context_block}]
    for msg in request.messages:
        msgs.append({"role": msg.role, "content": msg.content})
    return msgs


async def _call_openai(messages: list[dict]) -> str:
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        )
        data = resp.json()
        if "error" in data:
            return _fallback_response(messages[-1]["content"], {})
        return data["choices"][0]["message"]["content"]


def _fallback_response(question: str, context: dict[str, Any]) -> str:
    """Rule-based responses when no OpenAI key is configured."""
    q = question.lower()
    city = context.get("selected_city", {})
    prediction = context.get("prediction", {})
    competitors = context.get("competitors", {})
    seasonality = context.get("seasonality", {})
    market = context.get("market_insights", {})

    city_name = city.get("city", "this location")

    if any(w in q for w in ["revenue", "earn", "sales", "money", "income"]):
        rev = prediction.get("predicted_annual_revenue_eur", 0)
        if rev:
            return (
                f"Based on our ML model, a Meller store in **{city_name}** is projected to generate "
                f"**€{rev:,.0f}/year** (range: €{prediction.get('confidence_interval_low', 0):,.0f} – "
                f"€{prediction.get('confidence_interval_high', 0):,.0f}). "
                f"Viability score: {prediction.get('viability_score', 'N/A')}/100 — "
                f"{prediction.get('viability_label', 'N/A')}. "
                f"Revenue per m²: €{prediction.get('revenue_per_sqm', 0):,.0f}."
            )
        return f"Select a city on the map to see revenue projections for {city_name}."

    if any(w in q for w in ["competitor", "competition", "brand", "ray-ban", "oakley", "sunglasses"]):
        total = competitors.get("total_competitors", 0)
        brands = competitors.get("brands_present", [])
        assessment = competitors.get("market_assessment", "")
        opp = competitors.get("meller_opportunity_score", 0)
        brand_list = ", ".join(brands[:8]) if brands else "various eyewear retailers"
        return (
            f"In **{city_name}**, we identify **{total} competitor stores** including {brand_list}. "
            f"Market saturation: {competitors.get('market_saturation_score', 0)}/100. "
            f"Meller opportunity score: **{opp}/100**. {assessment}"
        )

    if any(w in q for w in ["season", "tourist", "summer", "winter", "monthly", "peak"]):
        peak = market.get("peak_season", seasonality.get("peak_month", "July"))
        low = market.get("low_season", seasonality.get("low_month", "February"))
        summer_share = market.get("summer_revenue_share", 0)
        is_tourist = market.get("is_tourist_destination", False)
        return (
            f"**{city_name}** seasonal profile: Peak season is **{peak}**, lowest is **{low}**. "
            f"{'This is a major tourist destination — ' if is_tourist else ''}"
            f"Summer accounts for ~{summer_share}% of annual revenue. "
            f"Recommended store opening: **{market.get('recommended_opening_month', 'September')}**. "
            f"Holiday boost: {market.get('holiday_boost', 'Q4 gifting season')}."
        )

    if any(w in q for w in ["store", "size", "location", "google", "maps", "address"]):
        stores = context.get("meller_stores", [])
        if stores:
            store = stores[0]
            return (
                f"Found Meller store near **{city_name}**: {store.get('name', 'Meller Store')} "
                f"at {store.get('address', 'N/A')}. "
                f"Estimated size: ~{store.get('estimated_size_sqm', 80)}m². "
                f"Rating: {store.get('rating', 'N/A')}/5 ({store.get('user_ratings_total', 0)} reviews)."
            )
        return (
            f"No existing Meller store found near **{city_name}** via Google Maps. "
            f"This could be a greenfield opportunity. "
            f"Set GOOGLE_MAPS_API_KEY for live store data."
        )

    if any(w in q for w in ["recommend", "should", "open", "expand", "best"]):
        score = prediction.get("viability_score", 0)
        label = prediction.get("viability_label", "")
        rec = prediction.get("recommendation", "")
        if rec:
            return rec
        return (
            f"For **{city_name}**: viability is **{score}/100** ({label}). "
            f"Consider a 80-100m² store in a high foot-traffic area near luxury retail. "
            f"Analyze competitors and seasonal patterns in the sidebar for full context."
        )

    if any(w in q for w in ["market", "estimate", "potential", "opportunity"]):
        opp = competitors.get("meller_opportunity_score", 0)
        saturation = competitors.get("market_saturation_score", 0)
        gdp = city.get("gdp_per_capita", 0)
        pop = city.get("population", 0)
        return (
            f"**{city_name}** market overview: Population {pop:,}, GDP/capita €{gdp:,}. "
            f"Market saturation {saturation}/100, Meller opportunity {opp}/100. "
            f"{competitors.get('market_assessment', '')} "
            f"{'Strong tourist market.' if market.get('is_tourist_destination') else 'Primarily local demand market.'}"
        )

    return (
        f"I can help analyze **{city_name}** for Meller store expansion. Ask me about:\n"
        f"- **Revenue projections** — expected annual sales\n"
        f"- **Competitors** — Ray-Ban, Oakley, and other sunglasses brands nearby\n"
        f"- **Seasonality** — peak months, tourist patterns\n"
        f"- **Store locations** — existing Meller stores via Google Maps\n"
        f"- **Market assessment** — opportunity and saturation scores\n\n"
        f"Select a city on the map for location-specific analysis. "
        f"Set OPENAI_API_KEY for full AI-powered responses."
    )


def _summarize_context(context: dict[str, Any]) -> list[str]:
    keys = []
    if context.get("selected_city"):
        keys.append("selected_city")
    if context.get("prediction"):
        keys.append("prediction")
    if context.get("competitors"):
        keys.append("competitors")
    if context.get("seasonality"):
        keys.append("seasonality")
    if context.get("market_insights"):
        keys.append("market_insights")
    if context.get("meller_stores"):
        keys.append("meller_stores")
    return keys
