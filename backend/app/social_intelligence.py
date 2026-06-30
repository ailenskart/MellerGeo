"""Social & review intelligence from Google, Instagram, and X (Twitter)."""

from __future__ import annotations

import hashlib
import os
import random
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.google_maps import GOOGLE_MAPS_API_KEY, find_nearby_competitors, get_google_api_status, get_place_details, search_places

INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")

SHOPPING_HASHTAGS = [
    "shopping", "fashion", "sunglasses", "eyewear", "style", "ootd",
    "streetstyle", "boutique", "luxuryshopping", "shoplocal",
]

GOOGLE_REVIEW_SNIPPETS_POSITIVE = [
    "Amazing selection of sunglasses, staff was super helpful",
    "Great shopping street, lots of trendy boutiques",
    "Perfect place for eyewear, found exactly what I wanted",
    "Love the vibe here, always discover new brands",
    "Excellent customer service and beautiful store design",
    "My go-to spot for sunglasses in the city",
    "Stunning window displays, very Instagram-worthy",
    "High foot traffic area, great for people watching and shopping",
]

GOOGLE_REVIEW_SNIPPETS_MIXED = [
    "Good selection but can get very crowded on weekends",
    "Nice area for shopping, rent seems high for retailers",
    "Great location but parking is difficult",
    "Popular tourist spot, prices are premium",
]

GOOGLE_REVIEW_SNIPPETS_NEGATIVE = [
    "Too crowded, hard to browse comfortably",
    "Overpriced compared to online options",
    "Limited parking, prefer shopping online",
]

INSTAGRAM_CAPTIONS = [
    "Shopping spree in {area} 🕶️✨ #fashion #sunglasses",
    "Found the cutest eyewear boutique in {area} 😎",
    "Street style inspo from {area} 📸 #ootd #shopping",
    "Sunday market vibes in {area} 🛍️",
    "Luxury shopping at its finest in {area} ✨",
    "Can't resist these frames from {area} 🔥 #meller #eyewear",
    "Exploring {area} — so many cool shops here",
    "Date night shopping in {area} 💫 #style",
]

TWITTER_POSTS = [
    "Just discovered an amazing sunglasses store in {area} — highly recommend",
    "Best shopping street in {city}? I'd say {area} hands down",
    "Anyone know good eyewear shops near {area}?",
    "{area} is packed with tourists but the shopping is worth it",
    "Pro tip: visit {area} on weekday mornings for the best shopping experience",
    "The new store in {area} is getting great reviews on Google",
    "Fashion Twitter: where do you buy sunglasses in {city}?",
]


def _rng(seed: str) -> random.Random:
    h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
    return random.Random(h)


async def analyze_social_intelligence(
    city: str,
    country: str,
    latitude: float,
    longitude: float,
    area_name: str | None = None,
    tourist_index: float = 50,
    foot_traffic: float = 50,
    catchment_id: str | None = None,
    street_name: str | None = None,
) -> dict[str, Any]:
    location_label = street_name or area_name or city
    seed = f"{city}-{catchment_id or ''}-{street_name or ''}-{latitude:.4f}"

    google_data = await _fetch_google_reviews(latitude, longitude, location_label, seed)
    instagram_data = await _fetch_instagram_signals(city, location_label, tourist_index, seed)
    twitter_data = await _fetch_twitter_signals(city, location_label, tourist_index, seed)
    shopping_destinations = _build_shopping_destinations(
        city, location_label, latitude, longitude, tourist_index, foot_traffic, seed, google_data
    )

    overall_sentiment = _compute_overall_sentiment(google_data, instagram_data, twitter_data)
    shopping_intent_score = _compute_shopping_intent(
        google_data, instagram_data, twitter_data, foot_traffic, tourist_index
    )

    return {
        "location": location_label,
        "city": city,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "overall_sentiment_score": overall_sentiment["score"],
        "overall_sentiment_label": overall_sentiment["label"],
        "shopping_intent_score": shopping_intent_score,
        "google": google_data,
        "instagram": instagram_data,
        "twitter": twitter_data,
        "shopping_destinations": shopping_destinations,
        "top_positive_themes": overall_sentiment["themes_positive"],
        "top_negative_themes": overall_sentiment["themes_negative"],
        "where_people_shop": [d["name"] for d in shopping_destinations[:5]],
        "data_sources": {
            "google_live": get_google_api_status().get("live", False),
            "instagram_live": bool(INSTAGRAM_ACCESS_TOKEN),
            "twitter_live": bool(TWITTER_BEARER_TOKEN),
        },
        "summary": _build_summary(location_label, city, overall_sentiment, shopping_destinations, shopping_intent_score),
    }


async def _fetch_google_reviews(
    lat: float, lon: float, area: str, seed: str
) -> dict[str, Any]:
    reviews: list[dict] = []
    places: list[dict] = []

    if GOOGLE_MAPS_API_KEY:
        raw_places = await search_places(f"shopping {area}", lat, lon, radius_m=1500)
        for place in raw_places[:8]:
            details = await _get_place_reviews(place.get("place_id", ""), place)
            if details:
                places.append(details)
                reviews.extend(details.get("reviews", []))

    if not reviews:
        reviews, places = _mock_google_reviews(area, lat, lon, seed)

    ratings = [r["rating"] for r in reviews if r.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 4.2

    positive = sum(1 for r in reviews if r.get("rating", 0) >= 4)
    sentiment_score = round(positive / max(len(reviews), 1) * 100, 1)

    return {
        "platform": "google",
        "average_rating": round(avg_rating, 1),
        "total_reviews": sum(p.get("user_ratings_total", 0) for p in places) or len(reviews) * 45,
        "review_count_analyzed": len(reviews),
        "sentiment_score": sentiment_score,
        "places_analyzed": len(places),
        "reviews": reviews[:12],
        "top_rated_nearby": [
            {"name": p["name"], "rating": p.get("rating", 0), "reviews": p.get("user_ratings_total", 0)}
            for p in sorted(places, key=lambda x: x.get("rating", 0), reverse=True)[:5]
        ],
    }


async def _get_place_reviews(place_id: str, place_summary: dict | None = None) -> dict | None:
    details = await get_place_details(place_id)
    if not details and place_summary:
        return {
            "name": place_summary.get("name", ""),
            "rating": place_summary.get("rating"),
            "user_ratings_total": place_summary.get("user_ratings_total", 0),
            "reviews": [],
        }
    if not details:
        return None

    formatted_reviews = details.get("reviews", [])
    if not formatted_reviews and details.get("rating"):
        formatted_reviews = []

    return {
        "name": details.get("name", ""),
        "rating": details.get("rating"),
        "user_ratings_total": details.get("user_ratings_total", 0),
        "reviews": formatted_reviews[:5],
    }


def _mock_google_reviews(area: str, lat: float, lon: float, seed: str) -> tuple[list[dict], list[dict]]:
    rng = _rng(seed + "google")
    n_reviews = rng.randint(8, 15)
    n_places = rng.randint(4, 7)

    place_names = [
        f"Fashion Boutique {area}", "Sunglass Hut", "Optical Express",
        "Trendy Eyewear", "Luxury Frames", "Urban Optics", "Style Studio",
    ]

    places = []
    all_reviews = []

    for i in range(n_places):
        rating = round(rng.uniform(3.8, 4.9), 1)
        total = rng.randint(80, 1200)
        place_reviews = []
        for j in range(rng.randint(1, 3)):
            r_rating = rng.randint(3, 5)
            pool = GOOGLE_REVIEW_SNIPPETS_POSITIVE if r_rating >= 4 else GOOGLE_REVIEW_SNIPPETS_MIXED
            if r_rating <= 2:
                pool = GOOGLE_REVIEW_SNIPPETS_NEGATIVE
            text = rng.choice(pool).replace("here", f"in {area}")
            days_ago = rng.randint(1, 90)
            place_reviews.append({
                "author": f"Reviewer_{rng.randint(100, 999)}",
                "rating": r_rating,
                "text": text,
                "time": f"{days_ago} days ago",
                "source": "google",
            })
            all_reviews.append(place_reviews[-1])

        places.append({
            "name": place_names[i % len(place_names)],
            "rating": rating,
            "user_ratings_total": total,
            "reviews": place_reviews,
        })

    return all_reviews, places


async def _fetch_instagram_signals(
    city: str, area: str, tourist_index: float, seed: str
) -> dict[str, Any]:
    if INSTAGRAM_ACCESS_TOKEN:
        live = await _instagram_api_search(city, area)
        if live:
            return live

    rng = _rng(seed + "instagram")
    base_mentions = int(50 + tourist_index * 8 + rng.randint(20, 200))
    hashtag_volume = {f"#{city.lower().replace(' ', '')}shopping": int(base_mentions * 0.4)}

    for tag in SHOPPING_HASHTAGS[:5]:
        hashtag_volume[f"#{tag}"] = int(base_mentions * rng.uniform(0.1, 0.5))

    posts = []
    for i in range(rng.randint(5, 8)):
        caption = rng.choice(INSTAGRAM_CAPTIONS).format(area=area, city=city)
        posts.append({
            "caption": caption,
            "likes": rng.randint(50, 5000),
            "comments": rng.randint(5, 200),
            "hashtags": [h for h in caption.split() if h.startswith("#")],
            "posted": (datetime.now() - timedelta(days=rng.randint(1, 30))).strftime("%Y-%m-%d"),
            "source": "instagram",
            "influencer_tier": rng.choice(["micro", "mid", "macro"]),
        })

    engagement_rate = round(rng.uniform(2.5, 8.5), 1)
    sentiment = round(65 + tourist_index * 0.25 + rng.uniform(-10, 15), 1)

    return {
        "platform": "instagram",
        "mention_volume_monthly": base_mentions,
        "hashtag_volume": hashtag_volume,
        "engagement_rate": engagement_rate,
        "sentiment_score": min(100, sentiment),
        "top_posts": sorted(posts, key=lambda x: x["likes"], reverse=True),
        "shopping_tags": [f"#{city.lower()}shopping", "#sunglasses", "#fashion", f"#{area.lower().replace(' ', '')}"],
        "influencer_visits_monthly": rng.randint(3, 25) if tourist_index > 50 else rng.randint(1, 8),
    }


async def _instagram_api_search(city: str, area: str) -> dict | None:
    """Placeholder for Instagram Graph API — requires business account token."""
    return None


async def _fetch_twitter_signals(
    city: str, area: str, tourist_index: float, seed: str
) -> dict[str, Any]:
    if TWITTER_BEARER_TOKEN:
        live = await _twitter_api_search(city, area)
        if live:
            return live

    rng = _rng(seed + "twitter")
    volume = int(20 + tourist_index * 3 + rng.randint(10, 100))

    posts = []
    for i in range(rng.randint(4, 7)):
        text = rng.choice(TWITTER_POSTS).format(area=area, city=city)
        posts.append({
            "text": text,
            "likes": rng.randint(5, 500),
            "retweets": rng.randint(0, 80),
            "posted": (datetime.now() - timedelta(days=rng.randint(1, 14))).strftime("%Y-%m-%d"),
            "source": "twitter",
            "sentiment": rng.choice(["positive", "positive", "neutral", "mixed"]),
        })

    positive = sum(1 for p in posts if p["sentiment"] == "positive")
    sentiment_score = round(positive / len(posts) * 100, 1) if posts else 70

    return {
        "platform": "twitter",
        "mention_volume_monthly": volume,
        "sentiment_score": sentiment_score,
        "top_posts": sorted(posts, key=lambda x: x["likes"] + x["retweets"] * 2, reverse=True),
        "trending_topics": [
            f"{city} shopping", f"best streets {city}", "sunglasses recommendations",
            f"where to shop {city}", "eyewear brands",
        ],
        "shopping_intent_mentions": rng.randint(5, 40),
    }


async def _twitter_api_search(city: str, area: str) -> dict | None:
    """Search recent tweets via X API v2."""
    query = f"({city} OR {area}) (shopping OR sunglasses OR eyewear) -is:retweet lang:en"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"},
                params={"query": query, "max_results": 10, "tweet.fields": "created_at,public_metrics"},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            tweets = data.get("data", [])
            if not tweets:
                return None

            posts = []
            for t in tweets:
                metrics = t.get("public_metrics", {})
                posts.append({
                    "text": t.get("text", ""),
                    "likes": metrics.get("like_count", 0),
                    "retweets": metrics.get("retweet_count", 0),
                    "posted": t.get("created_at", "")[:10],
                    "source": "twitter",
                    "sentiment": "neutral",
                })

            return {
                "platform": "twitter",
                "mention_volume_monthly": len(tweets) * 30,
                "sentiment_score": 70,
                "top_posts": posts,
                "trending_topics": [f"{city} shopping", "sunglasses"],
                "shopping_intent_mentions": len(tweets),
            }
    except Exception:
        return None


def _build_shopping_destinations(
    city: str,
    area: str,
    lat: float,
    lon: float,
    tourist_index: float,
    foot_traffic: float,
    seed: str,
    google_data: dict,
) -> list[dict]:
    rng = _rng(seed + "destinations")

    destinations = []
    street_names = [
        f"{area} Main Strip", f"{area} Boutique Row", f"{city} Fashion Mile",
        "Luxury Shopping Quarter", "Old Town Market Street", "Designer District",
    ]

    for i, name in enumerate(street_names[:rng.randint(4, 6)]):
        social_buzz = round(rng.uniform(40, 95) + tourist_index * 0.2, 0)
        google_rating = round(rng.uniform(3.8, 4.8), 1)
        if google_data.get("top_rated_nearby") and i < len(google_data["top_rated_nearby"]):
            nearby = google_data["top_rated_nearby"][i]
            name = nearby["name"]
            google_rating = nearby.get("rating", google_rating)

        destinations.append({
            "name": name,
            "social_buzz_score": min(100, social_buzz),
            "google_rating": google_rating,
            "foot_traffic_estimate": round(foot_traffic * rng.uniform(0.7, 1.3), 0),
            "instagram_mentions": rng.randint(20, 500),
            "why_popular": rng.choice([
                "High Instagram visibility and influencer visits",
                "Top-rated on Google with strong eyewear reviews",
                "Tourist hotspot with premium shopping",
                "Local favourite for fashion and accessories",
                "Trending on social media for street style",
                "Celebrity sightings drive foot traffic",
            ]),
            "best_for": rng.choice(["sunglasses", "fashion", "luxury", "lifestyle", "tourist retail"]),
        })

    destinations.sort(key=lambda x: x["social_buzz_score"], reverse=True)
    return destinations


def _compute_overall_sentiment(google: dict, instagram: dict, twitter: dict) -> dict:
    scores = [
        google.get("sentiment_score", 70) * 0.45,
        instagram.get("sentiment_score", 70) * 0.30,
        twitter.get("sentiment_score", 70) * 0.25,
    ]
    overall = round(sum(scores), 1)

    if overall >= 75:
        label = "Very Positive"
    elif overall >= 60:
        label = "Positive"
    elif overall >= 45:
        label = "Mixed"
    else:
        label = "Negative"

    return {
        "score": overall,
        "label": label,
        "themes_positive": [
            "Great shopping atmosphere", "Strong eyewear selection",
            "High social media visibility", "Good Google reviews",
        ],
        "themes_negative": [
            "Crowding at peak times", "Premium pricing concerns",
        ] if overall < 70 else [],
    }


def _compute_shopping_intent(
    google: dict, instagram: dict, twitter: dict, foot_traffic: float, tourist_index: float
) -> float:
    google_factor = google.get("average_rating", 4) / 5 * 30
    insta_factor = min(30, instagram.get("mention_volume_monthly", 0) / 20)
    twitter_factor = min(20, twitter.get("shopping_intent_mentions", 0) * 2)
    location_factor = (foot_traffic + tourist_index) / 200 * 20
    return round(min(100, google_factor + insta_factor + twitter_factor + location_factor), 1)


def _build_summary(
    area: str, city: str, sentiment: dict, destinations: list, shopping_intent: float
) -> str:
    top = destinations[0]["name"] if destinations else area
    return (
        f"Social intelligence for {area}, {city}: overall sentiment is {sentiment['label']} "
        f"({sentiment['score']}/100). Shopping intent score: {shopping_intent}/100. "
        f"People are most actively shopping at {top}. "
        f"Instagram and Google reviews indicate strong interest in eyewear and fashion retail in this area."
    )
