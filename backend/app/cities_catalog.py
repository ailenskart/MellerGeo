"""European cities catalog — 200+ cities for Meller expansion analysis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.meller_stores import MELLER_STORE_CITIES

# Country defaults: (gdp_per_capita_eur, tier_1_cities, tier_2_cities, tier_3_cities)
COUNTRY_CITIES: dict[str, dict] = {
    "Spain": {
        "gdp": 32500,
        "cities": [
            ("Madrid", 40.4168, -3.7038, 3280000, 1),
            ("Barcelona", 41.3851, 2.1734, 1620000, 1),
            ("Valencia", 39.4699, -0.3763, 800000, 2),
            ("Seville", 37.3891, -5.9845, 690000, 2),
            ("Bilbao", 43.2630, -2.9350, 350000, 2),
            ("Malaga", 36.7213, -4.4214, 580000, 2),
            ("Zaragoza", 41.6488, -0.8891, 680000, 2),
            ("Palma", 39.5696, 2.6502, 420000, 2),
            ("Murcia", 37.9922, -1.1307, 460000, 3),
            ("Alicante", 38.3452, -0.4810, 340000, 3),
            ("Granada", 37.1773, -3.5986, 240000, 3),
            ("San Sebastian", 43.3183, -1.9812, 190000, 3),
            ("Santander", 43.4623, -3.8100, 180000, 3),
            ("Vigo", 42.2406, -8.7207, 300000, 3),
            ("Cordoba", 37.8882, -4.7794, 330000, 3),
            ("Ibiza Town", 38.9067, 1.4206, 50000, 3),
        ],
    },
    "France": {
        "gdp": 42800,
        "cities": [
            ("Paris", 48.8566, 2.3522, 2160000, 1),
            ("Lyon", 45.7640, 4.8357, 520000, 2),
            ("Marseille", 43.2965, 5.3698, 870000, 2),
            ("Nice", 43.7102, 7.2620, 340000, 2),
            ("Toulouse", 43.6047, 1.4442, 480000, 2),
            ("Bordeaux", 44.8378, -0.5792, 260000, 2),
            ("Lille", 50.6292, 3.0573, 235000, 2),
            ("Nantes", 47.2184, -1.5536, 320000, 2),
            ("Strasbourg", 48.5734, 7.7521, 290000, 2),
            ("Montpellier", 43.6108, 3.8767, 300000, 2),
            ("Rennes", 48.1173, -1.6778, 220000, 3),
            ("Grenoble", 45.1885, 5.7245, 160000, 3),
            ("Cannes", 43.5528, 7.0174, 75000, 3),
            ("Monaco", 43.7384, 7.4246, 39000, 3),
            ("Aix-en-Provence", 43.5297, 5.4474, 145000, 3),
        ],
    },
    "Germany": {
        "gdp": 45200,
        "cities": [
            ("Berlin", 52.5200, 13.4050, 3650000, 1),
            ("Munich", 48.1351, 11.5820, 1480000, 1),
            ("Hamburg", 53.5511, 9.9937, 1840000, 1),
            ("Frankfurt", 50.1109, 8.6821, 750000, 2),
            ("Cologne", 50.9375, 6.9603, 1080000, 2),
            ("Stuttgart", 48.7758, 9.1829, 630000, 2),
            ("Dusseldorf", 51.2277, 6.7735, 620000, 2),
            ("Leipzig", 51.3397, 12.3731, 600000, 2),
            ("Dresden", 51.0504, 13.7373, 560000, 2),
            ("Hannover", 52.3759, 9.7320, 540000, 2),
            ("Nuremberg", 49.4521, 11.0767, 520000, 2),
            ("Bremen", 53.0793, 8.8017, 570000, 3),
            ("Dortmund", 51.5136, 7.4653, 590000, 3),
            ("Essen", 51.4556, 7.0116, 580000, 3),
            ("Bonn", 50.7374, 7.0982, 330000, 3),
            ("Freiburg", 47.9990, 7.8421, 230000, 3),
            ("Heidelberg", 49.3988, 8.6724, 160000, 3),
        ],
    },
    "Italy": {
        "gdp": 35800,
        "cities": [
            ("Milan", 45.4642, 9.1900, 1350000, 1),
            ("Rome", 41.9028, 12.4964, 2870000, 1),
            ("Florence", 43.7696, 11.2558, 380000, 2),
            ("Naples", 40.8518, 14.2681, 960000, 2),
            ("Turin", 45.0703, 7.6869, 870000, 2),
            ("Venice", 45.4408, 12.3155, 260000, 2),
            ("Bologna", 44.4949, 11.3426, 390000, 2),
            ("Genoa", 44.4056, 8.9463, 580000, 2),
            ("Verona", 45.4384, 10.9916, 260000, 3),
            ("Palermo", 38.1157, 13.3615, 670000, 3),
            ("Catania", 37.5079, 15.0830, 310000, 3),
            ("Bari", 41.1171, 16.8719, 320000, 3),
            ("Rimini", 44.0678, 12.5695, 150000, 3),
            ("Como", 45.8081, 9.0852, 85000, 3),
            ("Capri", 40.5507, 14.2426, 7500, 3),
        ],
    },
    "United Kingdom": {
        "gdp": 48500,
        "cities": [
            ("London", 51.5074, -0.1278, 8960000, 1),
            ("Manchester", 53.4808, -2.2426, 550000, 2),
            ("Edinburgh", 55.9533, -3.1883, 530000, 2),
            ("Birmingham", 52.4862, -1.8904, 1140000, 2),
            ("Liverpool", 53.4084, -2.9916, 500000, 2),
            ("Bristol", 51.4545, -2.5879, 470000, 2),
            ("Leeds", 53.8008, -1.5491, 790000, 2),
            ("Glasgow", 55.8642, -4.2518, 635000, 2),
            ("Brighton", 50.8225, -0.1372, 290000, 3),
            ("Oxford", 51.7520, -1.2577, 160000, 3),
            ("Cambridge", 52.2053, 0.1218, 145000, 3),
            ("Bath", 51.3811, -2.3590, 95000, 3),
            ("York", 53.9591, -1.0815, 210000, 3),
            ("Belfast", 54.5973, -5.9301, 345000, 3),
            ("Cardiff", 51.4816, -3.1791, 370000, 3),
        ],
    },
    "Netherlands": {
        "gdp": 52800,
        "cities": [
            ("Amsterdam", 52.3676, 4.9041, 870000, 1),
            ("Rotterdam", 51.9244, 4.4777, 650000, 2),
            ("The Hague", 52.0705, 4.3007, 550000, 2),
            ("Utrecht", 52.0907, 5.1214, 360000, 2),
            ("Eindhoven", 51.4416, 5.4697, 240000, 3),
            ("Maastricht", 50.8514, 5.6910, 125000, 3),
            ("Groningen", 53.2194, 6.5665, 235000, 3),
        ],
    },
    "Belgium": {
        "gdp": 43600,
        "cities": [
            ("Brussels", 50.8503, 4.3517, 1210000, 1),
            ("Antwerp", 51.2194, 4.4025, 530000, 2),
            ("Ghent", 51.0543, 3.7174, 265000, 2),
            ("Bruges", 51.2093, 3.2247, 118000, 3),
            ("Liege", 50.6326, 5.5797, 200000, 3),
        ],
    },
    "Portugal": {
        "gdp": 28900,
        "cities": [
            ("Lisbon", 38.7223, -9.1393, 550000, 1),
            ("Porto", 41.1579, -8.6291, 240000, 2),
            ("Faro", 37.0194, -7.9322, 65000, 3),
            ("Cascais", 38.6979, -9.4215, 210000, 3),
            ("Funchal", 32.6669, -16.9241, 112000, 3),
        ],
    },
    "Austria": {
        "gdp": 50200,
        "cities": [
            ("Vienna", 48.2082, 16.3738, 1900000, 1),
            ("Salzburg", 47.8095, 13.0550, 155000, 2),
            ("Innsbruck", 47.2692, 11.4041, 132000, 3),
            ("Graz", 47.0707, 15.4395, 290000, 3),
        ],
    },
    "Switzerland": {
        "gdp": 78400,
        "cities": [
            ("Zurich", 47.3769, 8.5417, 430000, 1),
            ("Geneva", 46.2044, 6.1432, 200000, 2),
            ("Basel", 47.5596, 7.5886, 175000, 2),
            ("Bern", 46.9480, 7.4474, 135000, 3),
            ("Lausanne", 46.5197, 6.6323, 140000, 3),
            ("Lugano", 46.0037, 8.9511, 63000, 3),
            ("St. Moritz", 46.4908, 9.8355, 5000, 3),
        ],
    },
    "Denmark": {
        "gdp": 58600,
        "cities": [
            ("Copenhagen", 55.6761, 12.5683, 640000, 1),
            ("Aarhus", 56.1629, 10.2039, 280000, 2),
            ("Odense", 55.4038, 10.4024, 180000, 3),
        ],
    },
    "Sweden": {
        "gdp": 54300,
        "cities": [
            ("Stockholm", 59.3293, 18.0686, 980000, 1),
            ("Gothenburg", 57.7089, 11.9746, 580000, 2),
            ("Malmo", 55.6050, 13.0038, 350000, 2),
            ("Uppsala", 59.8588, 17.6389, 180000, 3),
        ],
    },
    "Norway": {
        "gdp": 72500,
        "cities": [
            ("Oslo", 59.9139, 10.7522, 700000, 1),
            ("Bergen", 60.3913, 5.3221, 285000, 2),
            ("Stavanger", 58.9700, 5.7331, 145000, 3),
            ("Trondheim", 63.4305, 10.3951, 210000, 3),
        ],
    },
    "Finland": {
        "gdp": 48900,
        "cities": [
            ("Helsinki", 60.1699, 24.9384, 660000, 1),
            ("Tampere", 61.4978, 23.7610, 245000, 2),
            ("Turku", 60.4518, 22.2666, 195000, 3),
        ],
    },
    "Ireland": {
        "gdp": 78200,
        "cities": [
            ("Dublin", 53.3498, -6.2603, 550000, 1),
            ("Cork", 51.8985, -8.4756, 210000, 2),
            ("Galway", 53.2707, -9.0568, 85000, 3),
        ],
    },
    "Poland": {
        "gdp": 22800,
        "cities": [
            ("Warsaw", 52.2297, 21.0122, 1790000, 1),
            ("Krakow", 50.0647, 19.9450, 780000, 2),
            ("Wroclaw", 51.1079, 17.0385, 640000, 2),
            ("Gdansk", 54.3520, 18.6466, 470000, 2),
            ("Poznan", 52.4064, 16.9252, 540000, 2),
            ("Lodz", 51.7592, 19.4560, 680000, 3),
            ("Katowice", 50.2649, 19.0238, 290000, 3),
        ],
    },
    "Czech Republic": {
        "gdp": 28600,
        "cities": [
            ("Prague", 50.0755, 14.4378, 1320000, 1),
            ("Brno", 49.1951, 16.6068, 380000, 2),
            ("Ostrava", 49.8209, 18.2625, 285000, 3),
            ("Karlovy Vary", 50.2319, 12.8719, 49000, 3),
        ],
    },
    "Hungary": {
        "gdp": 21400,
        "cities": [
            ("Budapest", 47.4979, 19.0402, 1750000, 1),
            ("Debrecen", 47.5316, 21.6273, 205000, 3),
            ("Szeged", 46.2530, 20.1414, 160000, 3),
        ],
    },
    "Greece": {
        "gdp": 24600,
        "cities": [
            ("Athens", 37.9838, 23.7275, 660000, 1),
            ("Thessaloniki", 40.6401, 22.9444, 320000, 2),
            ("Heraklion", 35.3387, 25.1442, 175000, 3),
            ("Santorini", 36.3932, 25.4615, 16000, 3),
            ("Mykonos", 37.4467, 25.3289, 12000, 3),
            ("Rhodes", 36.4341, 28.2176, 50000, 3),
        ],
    },
    "Romania": {
        "gdp": 16800,
        "cities": [
            ("Bucharest", 44.4268, 26.1025, 1800000, 1),
            ("Cluj-Napoca", 46.7712, 23.6236, 325000, 2),
            ("Timisoara", 45.7489, 21.2087, 320000, 3),
            ("Brasov", 45.6579, 25.6012, 250000, 3),
        ],
    },
    "Croatia": {
        "gdp": 20500,
        "cities": [
            ("Zagreb", 45.8150, 15.9819, 800000, 1),
            ("Split", 43.5081, 16.4402, 180000, 2),
            ("Dubrovnik", 42.6507, 18.0944, 43000, 3),
        ],
    },
    "Slovenia": {
        "gdp": 31200,
        "cities": [
            ("Ljubljana", 46.0569, 14.5058, 295000, 2),
        ],
    },
    "Slovakia": {
        "gdp": 22400,
        "cities": [
            ("Bratislava", 48.1486, 17.1077, 440000, 2),
            ("Kosice", 48.7164, 21.2611, 240000, 3),
        ],
    },
    "Bulgaria": {
        "gdp": 15400,
        "cities": [
            ("Sofia", 42.6977, 23.3219, 1300000, 1),
            ("Varna", 43.2141, 27.9147, 340000, 2),
            ("Plovdiv", 42.1354, 24.7453, 350000, 3),
        ],
    },
    "Serbia": {
        "gdp": 11200,
        "cities": [
            ("Belgrade", 44.7866, 20.4489, 1400000, 1),
            ("Novi Sad", 45.2671, 19.8335, 290000, 3),
        ],
    },
    "Luxembourg": {
        "gdp": 112000,
        "cities": [
            ("Luxembourg City", 49.6116, 6.1319, 125000, 2),
        ],
    },
    "Iceland": {
        "gdp": 68200,
        "cities": [
            ("Reykjavik", 64.1466, -21.9426, 135000, 2),
        ],
    },
    "Estonia": {
        "gdp": 28200,
        "cities": [
            ("Tallinn", 59.4370, 24.7536, 450000, 2),
        ],
    },
    "Latvia": {
        "gdp": 21800,
        "cities": [
            ("Riga", 56.9496, 24.1052, 630000, 2),
        ],
    },
    "Lithuania": {
        "gdp": 24800,
        "cities": [
            ("Vilnius", 54.6872, 25.2797, 590000, 2),
            ("Kaunas", 54.8985, 23.9036, 290000, 3),
        ],
    },
    "Malta": {
        "gdp": 35200,
        "cities": [
            ("Valletta", 35.8989, 14.5146, 6000, 3),
            ("Sliema", 35.9125, 14.5019, 17000, 3),
        ],
    },
    "Cyprus": {
        "gdp": 32400,
        "cities": [
            ("Nicosia", 35.1856, 33.3823, 330000, 2),
            ("Limassol", 34.6786, 33.0413, 240000, 3),
        ],
    },
    "Ukraine": {
        "gdp": 4800,
        "cities": [
            ("Kyiv", 50.4501, 30.5234, 2900000, 1),
            ("Lviv", 49.8397, 24.0297, 720000, 2),
            ("Odesa", 46.4825, 30.7233, 1000000, 2),
        ],
    },
    "Turkey": {
        "gdp": 14200,
        "cities": [
            ("Istanbul", 41.0082, 28.9784, 15460000, 1),
            ("Ankara", 39.9334, 32.8597, 5500000, 1),
            ("Izmir", 38.4192, 27.1287, 4400000, 2),
            ("Antalya", 36.8969, 30.7133, 1300000, 2),
            ("Bodrum", 37.0344, 27.4305, 180000, 3),
        ],
    },
}

TOURIST_CITIES = {
    "Paris", "Barcelona", "Rome", "Amsterdam", "Prague", "Vienna", "Florence",
    "Nice", "Lisbon", "Edinburgh", "Venice", "Monaco", "Cannes", "Ibiza Town",
    "Santorini", "Mykonos", "Dubrovnik", "Capri", "St. Moritz", "Bodrum",
    "Antalya", "Rhodes", "Palma", "Malaga", "Brighton", "Bruges", "Salzburg",
    "Cascais", "Funchal", "Split", "Karlovy Vary", "Rimini", "Sliema",
}

SUNGLASSES_BRANDS = [
    "Ray-Ban", "Oakley", "Persol", "Oliver Peoples", "Gentle Monster",
    "Maui Jim", "Tom Ford Eyewear", "Gucci Eyewear", "Prada Eyewear",
    "Warby Parker", "Quay Australia", "Celine Eyewear", "Dior Eyewear",
    "Fendi Eyewear", "Versace Eyewear", "Carrera", "Police", "Vogue Eyewear",
    "Hawkers", "Polette", "Ace & Tate", "MessyWeekend", "Meller",
]


def _city_id(city: str, country: str) -> str:
    slug = city.lower().replace(" ", "-").replace(".", "")
    country_code = hashlib.md5(country.encode()).hexdigest()[:4]
    return f"{slug}-{country_code}"


def build_europe_cities() -> list[dict]:
    cities = []
    for country, data in COUNTRY_CITIES.items():
        gdp = data["gdp"]
        for city, lat, lon, pop, tier in data["cities"]:
            cities.append({
                "city": city,
                "country": country,
                "lat": lat,
                "lon": lon,
                "pop": pop,
                "gdp": gdp,
                "tier": tier,
            })
    return cities


EUROPE_CITIES = build_europe_cities()


def is_tourist_city(city: str) -> bool:
    return city in TOURIST_CITIES


def has_meller_store(city: str) -> bool:
    return city in MELLER_STORE_CITIES
