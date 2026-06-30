"""Catchment areas and retail streets for city-level store placement analysis."""

from __future__ import annotations

import hashlib
import math

# Hand-crafted catchments and streets for key MELLER expansion cities.
# Each catchment: district-level area with polygon boundary.
# Each street: specific retail location candidate.

CITY_CATCHMENTS: dict[str, list[dict]] = {
    "Barcelona": [
        {
            "id": "bcn-gothic",
            "name": "Gothic Quarter (Barri Gòtic)",
            "type": "historic_tourist",
            "center": [41.3828, 2.1761],
            "polygon": [[41.379, 2.171], [41.379, 2.182], [41.386, 2.182], [41.386, 2.171]],
            "foot_traffic": 92, "tourist": 88, "luxury": 65, "rent": 78, "income_factor": 1.05,
            "has_meller_store": True,
        },
        {
            "id": "bcn-born",
            "name": "El Born",
            "type": "trendy_lifestyle",
            "center": [41.3850, 2.1830],
            "polygon": [[41.382, 2.179], [41.382, 2.188], [41.388, 2.188], [41.388, 2.179]],
            "foot_traffic": 85, "tourist": 75, "luxury": 72, "rent": 72, "income_factor": 1.08,
            "has_meller_store": True,
        },
        {
            "id": "bcn-eixample",
            "name": "Eixample",
            "type": "premium_shopping",
            "center": [41.3930, 2.1640],
            "polygon": [[41.388, 2.155], [41.388, 2.175], [41.398, 2.175], [41.398, 2.155]],
            "foot_traffic": 88, "tourist": 70, "luxury": 90, "rent": 85, "income_factor": 1.15,
        },
        {
            "id": "bcn-passeig-gracia",
            "name": "Passeig de Gràcia",
            "type": "luxury_boulevard",
            "center": [41.3950, 2.1610],
            "polygon": [[41.392, 2.158], [41.392, 2.168], [41.398, 2.168], [41.398, 2.158]],
            "foot_traffic": 82, "tourist": 65, "luxury": 95, "rent": 92, "income_factor": 1.25,
        },
        {
            "id": "bcn-gracia",
            "name": "Gràcia",
            "type": "local_creative",
            "center": [41.4030, 2.1580],
            "polygon": [[41.399, 2.152], [41.399, 2.165], [41.407, 2.165], [41.407, 2.152]],
            "foot_traffic": 68, "tourist": 40, "luxury": 55, "rent": 58, "income_factor": 1.0,
        },
        {
            "id": "bcn-barceloneta",
            "name": "Barceloneta",
            "type": "beach_tourist",
            "center": [41.3780, 2.1890],
            "polygon": [[41.375, 2.185], [41.375, 2.195], [41.381, 2.195], [41.381, 2.185]],
            "foot_traffic": 75, "tourist": 90, "luxury": 45, "rent": 70, "income_factor": 0.9,
        },
        {
            "id": "bcn-diagonal-mar",
            "name": "Diagonal Mar",
            "type": "mall_modern",
            "center": [41.4100, 2.2160],
            "polygon": [[41.406, 2.210], [41.406, 2.222], [41.414, 2.222], [41.414, 2.210]],
            "foot_traffic": 70, "tourist": 35, "luxury": 60, "rent": 55, "income_factor": 1.02,
        },
    ],
    "Paris": [
        {
            "id": "par-marais",
            "name": "Le Marais",
            "type": "historic_fashion",
            "center": [48.8570, 2.3590],
            "polygon": [[48.853, 2.352], [48.853, 2.366], [48.861, 2.366], [48.861, 2.352]],
            "foot_traffic": 90, "tourist": 82, "luxury": 80, "rent": 88, "income_factor": 1.12,
            "has_meller_store": True,
        },
        {
            "id": "par-champs",
            "name": "Champs-Élysées",
            "type": "luxury_boulevard",
            "center": [48.8698, 2.3078],
            "polygon": [[48.867, 2.300], [48.867, 2.315], [48.873, 2.315], [48.873, 2.300]],
            "foot_traffic": 95, "tourist": 92, "luxury": 98, "rent": 98, "income_factor": 1.35,
        },
        {
            "id": "par-saint-germain",
            "name": "Saint-Germain-des-Prés",
            "type": "premium_lifestyle",
            "center": [48.8530, 2.3330],
            "polygon": [[48.849, 2.326], [48.849, 2.340], [48.857, 2.340], [48.857, 2.326]],
            "foot_traffic": 78, "tourist": 70, "luxury": 88, "rent": 90, "income_factor": 1.22,
        },
        {
            "id": "par-opera",
            "name": "Opéra / Grands Boulevards",
            "type": "department_retail",
            "center": [48.8720, 2.3320],
            "polygon": [[48.868, 2.325], [48.868, 2.340], [48.876, 2.340], [48.876, 2.325]],
            "foot_traffic": 88, "tourist": 60, "luxury": 75, "rent": 82, "income_factor": 1.1,
        },
        {
            "id": "par-montmartre",
            "name": "Montmartre",
            "type": "tourist_artistic",
            "center": [48.8867, 2.3431],
            "polygon": [[48.882, 2.336], [48.882, 2.350], [48.891, 2.350], [48.891, 2.336]],
            "foot_traffic": 80, "tourist": 95, "luxury": 50, "rent": 75, "income_factor": 0.95,
        },
        {
            "id": "par-bastille",
            "name": "Bastille / République",
            "type": "young_urban",
            "center": [48.8530, 2.3690],
            "polygon": [[48.849, 2.362], [48.849, 2.376], [48.857, 2.376], [48.857, 2.362]],
            "foot_traffic": 72, "tourist": 45, "luxury": 55, "rent": 65, "income_factor": 1.0,
        },
    ],
    "Amsterdam": [
        {
            "id": "ams-kalverstraat",
            "name": "Kalverstraat / Damrak",
            "type": "prime_high_street",
            "center": [52.3670, 4.8900],
            "polygon": [[52.364, 4.888], [52.364, 4.895], [52.370, 4.895], [52.370, 4.888]],
            "foot_traffic": 94, "tourist": 85, "luxury": 70, "rent": 90, "income_factor": 1.15,
            "has_meller_store": True,
        },
        {
            "id": "ams-nine-streets",
            "name": "Nine Streets (De Negen Straatjes)",
            "type": "boutique_lifestyle",
            "center": [52.3700, 4.8830],
            "polygon": [[52.367, 4.878], [52.367, 4.888], [52.373, 4.888], [52.373, 4.878]],
            "foot_traffic": 78, "tourist": 65, "luxury": 82, "rent": 78, "income_factor": 1.18,
        },
        {
            "id": "ams-jordaan",
            "name": "Jordaan",
            "type": "local_creative",
            "center": [52.3740, 4.8800],
            "polygon": [[52.370, 4.874], [52.370, 4.886], [52.378, 4.886], [52.378, 4.874]],
            "foot_traffic": 65, "tourist": 50, "luxury": 60, "rent": 62, "income_factor": 1.05,
        },
        {
            "id": "ams-pc-hooft",
            "name": "PC Hooftstraat",
            "type": "luxury_fashion",
            "center": [52.3590, 4.8790],
            "polygon": [[52.356, 4.875], [52.356, 4.883], [52.362, 4.883], [52.362, 4.875]],
            "foot_traffic": 70, "tourist": 55, "luxury": 95, "rent": 88, "income_factor": 1.28,
        },
        {
            "id": "ams-de-pijp",
            "name": "De Pijp",
            "type": "young_urban",
            "center": [52.3550, 4.8950],
            "polygon": [[52.351, 4.889], [52.351, 4.901], [52.359, 4.901], [52.359, 4.889]],
            "foot_traffic": 68, "tourist": 40, "luxury": 45, "rent": 55, "income_factor": 0.98,
        },
    ],
    "London": [
        {"id": "lon-covent", "name": "Covent Garden", "type": "tourist_retail", "center": [51.5118, -0.1225], "polygon": [[51.508, -0.128], [51.508, -0.117], [51.515, -0.117], [51.515, -0.128]], "foot_traffic": 92, "tourist": 88, "luxury": 75, "rent": 92, "income_factor": 1.2},
        {"id": "lon-oxford", "name": "Oxford Street", "type": "prime_high_street", "center": [51.5154, -0.1415], "polygon": [[51.512, -0.148], [51.512, -0.135], [51.519, -0.135], [51.519, -0.148]], "foot_traffic": 98, "tourist": 80, "luxury": 70, "rent": 95, "income_factor": 1.15},
        {"id": "lon-kings-road", "name": "King's Road, Chelsea", "type": "premium_lifestyle", "center": [51.4875, -0.1687], "polygon": [[51.484, -0.175], [51.484, -0.162], [51.491, -0.162], [51.491, -0.175]], "foot_traffic": 72, "tourist": 45, "luxury": 88, "rent": 85, "income_factor": 1.25},
        {"id": "lon-shoreditch", "name": "Shoreditch", "type": "trendy_lifestyle", "center": [51.5250, -0.0780], "polygon": [[51.521, -0.084], [51.521, -0.072], [51.529, -0.072], [51.529, -0.084]], "foot_traffic": 75, "tourist": 35, "luxury": 55, "rent": 68, "income_factor": 1.05},
        {"id": "lon-mayfair", "name": "Mayfair / Bond Street", "type": "luxury_fashion", "center": [51.5130, -0.1480], "polygon": [[51.509, -0.154], [51.509, -0.142], [51.517, -0.142], [51.517, -0.154]], "foot_traffic": 68, "tourist": 55, "luxury": 98, "rent": 98, "income_factor": 1.4},
        {"id": "lon-carnaby", "name": "Carnaby Street", "type": "fashion_district", "center": [51.5135, -0.1385], "polygon": [[51.511, -0.142], [51.511, -0.135], [51.516, -0.135], [51.516, -0.142]], "foot_traffic": 85, "tourist": 70, "luxury": 72, "rent": 88, "income_factor": 1.12},
    ],
    "Milan": [
        {"id": "mil-quadrilatero", "name": "Quadrilatero della Moda", "type": "luxury_fashion", "center": [45.4680, 9.1950], "polygon": [[45.465, 9.190], [45.465, 9.200], [45.471, 9.200], [45.471, 9.190]], "foot_traffic": 75, "tourist": 70, "luxury": 98, "rent": 95, "income_factor": 1.35},
        {"id": "mil-duomo", "name": "Duomo / Corso Vittorio", "type": "prime_high_street", "center": [45.4640, 9.1900], "polygon": [[45.461, 9.184], [45.461, 9.196], [45.467, 9.196], [45.467, 9.184]], "foot_traffic": 95, "tourist": 90, "luxury": 80, "rent": 90, "income_factor": 1.18},
        {"id": "mil-brera", "name": "Brera", "type": "artistic_lifestyle", "center": [45.4720, 9.1880], "polygon": [[45.469, 9.182], [45.469, 9.194], [45.475, 9.194], [45.475, 9.182]], "foot_traffic": 70, "tourist": 55, "luxury": 75, "rent": 78, "income_factor": 1.1},
        {"id": "mil-navigli", "name": "Navigli", "type": "nightlife_lifestyle", "center": [45.4520, 9.1750], "polygon": [[45.448, 9.169], [45.448, 9.181], [45.456, 9.181], [45.456, 9.169]], "foot_traffic": 72, "tourist": 50, "luxury": 55, "rent": 62, "income_factor": 1.0},
        {"id": "mil-corso-buenos", "name": "Corso Buenos Aires", "type": "mass_retail", "center": [45.4780, 9.2100], "polygon": [[45.475, 9.204], [45.475, 9.216], [45.481, 9.216], [45.481, 9.204]], "foot_traffic": 88, "tourist": 40, "luxury": 45, "rent": 72, "income_factor": 0.95},
    ],
    "Berlin": [
        {"id": "ber-kurfurst", "name": "Kurfürstendamm", "type": "premium_shopping", "center": [52.5040, 13.3270], "polygon": [[52.500, 13.320], [52.500, 13.334], [52.508, 13.334], [52.508, 13.320]], "foot_traffic": 82, "tourist": 65, "luxury": 78, "rent": 80, "income_factor": 1.1},
        {"id": "ber-mitte", "name": "Mitte / Friedrichstraße", "type": "prime_high_street", "center": [52.5200, 13.3880], "polygon": [[52.516, 13.382], [52.516, 13.394], [52.524, 13.394], [52.524, 13.382]], "foot_traffic": 88, "tourist": 75, "luxury": 70, "rent": 85, "income_factor": 1.08},
        {"id": "ber-prenzlauer", "name": "Prenzlauer Berg", "type": "trendy_lifestyle", "center": [52.5380, 13.4200], "polygon": [[52.534, 13.414], [52.534, 13.426], [52.542, 13.426], [52.542, 13.414]], "foot_traffic": 70, "tourist": 35, "luxury": 50, "rent": 58, "income_factor": 1.02},
        {"id": "ber-kreuzberg", "name": "Kreuzberg", "type": "young_urban", "center": [52.4980, 13.4030], "polygon": [[52.494, 13.397], [52.494, 13.409], [52.502, 13.409], [52.502, 13.397]], "foot_traffic": 68, "tourist": 30, "luxury": 42, "rent": 52, "income_factor": 0.95},
    ],
    "Madrid": [
        {"id": "mad-gran-via", "name": "Gran Vía", "type": "prime_high_street", "center": [40.4200, -3.7050], "polygon": [[40.416, -3.712], [40.416, -3.698], [40.424, -3.698], [40.424, -3.712]], "foot_traffic": 92, "tourist": 78, "luxury": 72, "rent": 85, "income_factor": 1.1},
        {"id": "mad-salamanca", "name": "Salamanca (Golden Mile)", "type": "luxury_fashion", "center": [40.4280, -3.6850], "polygon": [[40.424, -3.692], [40.424, -3.678], [40.432, -3.678], [40.432, -3.692]], "foot_traffic": 72, "tourist": 50, "luxury": 95, "rent": 92, "income_factor": 1.3},
        {"id": "mad-malasaña", "name": "Malasaña", "type": "trendy_lifestyle", "center": [40.4260, -3.7050], "polygon": [[40.422, -3.711], [40.422, -3.699], [40.430, -3.699], [40.430, -3.711]], "foot_traffic": 75, "tourist": 40, "luxury": 55, "rent": 65, "income_factor": 1.0},
        {"id": "mad-sol", "name": "Puerta del Sol", "type": "tourist_hub", "center": [40.4169, -3.7035], "polygon": [[40.413, -3.709], [40.413, -3.698], [40.420, -3.698], [40.420, -3.709]], "foot_traffic": 95, "tourist": 92, "luxury": 60, "rent": 88, "income_factor": 1.05},
    ],
}

CITY_STREETS: dict[str, list[dict]] = {
    "Barcelona": [
        {"id": "bcn-st-portaferrissa", "name": "Carrer de la Portaferrissa", "catchment_id": "bcn-gothic", "lat": 41.3825, "lon": 2.1754, "type": "tourist_retail", "foot_traffic": 94, "rent_index": 80, "width_m": 8, "has_meller": True},
        {"id": "bcn-st-argenteria", "name": "Carrer de l'Argenteria", "catchment_id": "bcn-born", "lat": 41.3845, "lon": 2.1820, "type": "boutique_street", "foot_traffic": 86, "rent_index": 74, "width_m": 6, "has_meller": True},
        {"id": "bcn-st-passeig-gracia", "name": "Passeig de Gràcia", "catchment_id": "bcn-passeig-gracia", "lat": 41.3950, "lon": 2.1610, "type": "luxury_boulevard", "foot_traffic": 88, "rent_index": 95, "width_m": 30},
        {"id": "bcn-st-rambla", "name": "La Rambla", "catchment_id": "bcn-gothic", "lat": 41.3810, "lon": 2.1730, "type": "tourist_boulevard", "foot_traffic": 98, "rent_index": 90, "width_m": 20},
        {"id": "bcn-st-portal-angel", "name": "Portal de l'Àngel", "catchment_id": "bcn-gothic", "lat": 41.3870, "lon": 2.1720, "type": "shopping_street", "foot_traffic": 90, "rent_index": 85, "width_m": 12},
        {"id": "bcn-st-consell-cent", "name": "Carrer del Consell de Cent", "catchment_id": "bcn-eixample", "lat": 41.3930, "lon": 2.1640, "type": "local_commercial", "foot_traffic": 72, "rent_index": 68, "width_m": 15},
        {"id": "bcn-st-diagonal", "name": "Avinguda Diagonal", "catchment_id": "bcn-eixample", "lat": 41.3970, "lon": 2.1580, "type": "major_avenue", "foot_traffic": 78, "rent_index": 82, "width_m": 40},
    ],
    "Paris": [
        {"id": "par-st-rosiers", "name": "Rue des Rosiers", "catchment_id": "par-marais", "lat": 48.8570, "lon": 2.3590, "type": "boutique_street", "foot_traffic": 88, "rent_index": 86, "width_m": 5, "has_meller": True},
        {"id": "par-st-rivoli", "name": "Rue de Rivoli", "catchment_id": "par-marais", "lat": 48.8560, "lon": 2.3550, "type": "shopping_street", "foot_traffic": 85, "rent_index": 88, "width_m": 18},
        {"id": "par-st-champs", "name": "Champs-Élysées", "catchment_id": "par-champs", "lat": 48.8698, "lon": 2.3078, "type": "luxury_boulevard", "foot_traffic": 96, "rent_index": 98, "width_m": 35},
        {"id": "par-st-saint-honore", "name": "Rue Saint-Honoré", "catchment_id": "par-saint-germain", "lat": 48.8650, "lon": 2.3300, "type": "luxury_fashion", "foot_traffic": 75, "rent_index": 92, "width_m": 10},
        {"id": "par-st-montorgueil", "name": "Rue Montorgueil", "catchment_id": "par-opera", "lat": 48.8640, "lon": 2.3470, "type": "pedestrian_market", "foot_traffic": 82, "rent_index": 78, "width_m": 8},
        {"id": "par-st-capucines", "name": "Boulevard des Capucines", "catchment_id": "par-opera", "lat": 48.8700, "lon": 2.3320, "type": "boulevard_retail", "foot_traffic": 78, "rent_index": 85, "width_m": 25},
    ],
    "Amsterdam": [
        {"id": "ams-st-kalverstraat", "name": "Kalverstraat", "catchment_id": "ams-kalverstraat", "lat": 52.3670, "lon": 4.8900, "type": "prime_high_street", "foot_traffic": 96, "rent_index": 92, "width_m": 10, "has_meller": True},
        {"id": "ams-st-damrak", "name": "Damrak", "catchment_id": "ams-kalverstraat", "lat": 52.3750, "lon": 4.8970, "type": "tourist_boulevard", "foot_traffic": 94, "rent_index": 88, "width_m": 15},
        {"id": "ams-st-harten", "name": "Hartenstraat", "catchment_id": "ams-nine-streets", "lat": 52.3700, "lon": 4.8830, "type": "boutique_street", "foot_traffic": 76, "rent_index": 80, "width_m": 5},
        {"id": "ams-st-pc-hooft", "name": "PC Hooftstraat", "catchment_id": "ams-pc-hooft", "lat": 52.3590, "lon": 4.8790, "type": "luxury_fashion", "foot_traffic": 72, "rent_index": 95, "width_m": 12},
        {"id": "ams-st-leidsestraat", "name": "Leidsestraat", "catchment_id": "ams-kalverstraat", "lat": 52.3660, "lon": 4.8850, "type": "shopping_street", "foot_traffic": 82, "rent_index": 78, "width_m": 8},
    ],
    "London": [
        {"id": "lon-st-oxford", "name": "Oxford Street", "catchment_id": "lon-oxford", "lat": 51.5154, "lon": -0.1415, "type": "prime_high_street", "foot_traffic": 98, "rent_index": 96, "width_m": 25},
        {"id": "lon-st-regent", "name": "Regent Street", "catchment_id": "lon-oxford", "lat": 51.5130, "lon": -0.1380, "type": "premium_shopping", "foot_traffic": 90, "rent_index": 92, "width_m": 20},
        {"id": "lon-st-bond", "name": "Bond Street", "catchment_id": "lon-mayfair", "lat": 51.5130, "lon": -0.1480, "type": "luxury_fashion", "foot_traffic": 70, "rent_index": 98, "width_m": 10},
        {"id": "lon-st-kings", "name": "King's Road", "catchment_id": "lon-kings-road", "lat": 51.4875, "lon": -0.1687, "type": "lifestyle_street", "foot_traffic": 74, "rent_index": 82, "width_m": 15},
        {"id": "lon-st-carnaby", "name": "Carnaby Street", "catchment_id": "lon-carnaby", "lat": 51.5135, "lon": -0.1385, "type": "fashion_district", "foot_traffic": 86, "rent_index": 88, "width_m": 8},
        {"id": "lon-st-covent", "name": "James Street, Covent Garden", "catchment_id": "lon-covent", "lat": 51.5118, "lon": -0.1225, "type": "pedestrian_plaza", "foot_traffic": 88, "rent_index": 90, "width_m": 12},
    ],
    "Milan": [
        {"id": "mil-st-montenapoleone", "name": "Via Montenapoleone", "catchment_id": "mil-quadrilatero", "lat": 45.4680, "lon": 9.1950, "type": "luxury_fashion", "foot_traffic": 72, "rent_index": 98, "width_m": 8},
        {"id": "mil-st-corso-vittorio", "name": "Corso Vittorio Emanuele II", "catchment_id": "mil-duomo", "lat": 45.4640, "lon": 9.1900, "type": "pedestrian_shopping", "foot_traffic": 94, "rent_index": 90, "width_m": 15},
        {"id": "mil-st-torino", "name": "Via Torino", "catchment_id": "mil-duomo", "lat": 45.4620, "lon": 9.1880, "type": "shopping_street", "foot_traffic": 88, "rent_index": 82, "width_m": 10},
        {"id": "mil-st-buenos-aires", "name": "Corso Buenos Aires", "catchment_id": "mil-corso-buenos", "lat": 45.4780, "lon": 9.2100, "type": "mass_retail", "foot_traffic": 85, "rent_index": 72, "width_m": 18},
        {"id": "mil-st-brera", "name": "Via Brera", "catchment_id": "mil-brera", "lat": 45.4720, "lon": 9.1880, "type": "artistic_boutique", "foot_traffic": 68, "rent_index": 75, "width_m": 6},
    ],
    "Berlin": [
        {"id": "ber-st-kurfurst", "name": "Kurfürstendamm", "catchment_id": "ber-kurfurst", "lat": 52.5040, "lon": 13.3270, "type": "premium_shopping", "foot_traffic": 84, "rent_index": 82, "width_m": 30},
        {"id": "ber-st-friedrich", "name": "Friedrichstraße", "catchment_id": "ber-mitte", "lat": 52.5200, "lon": 13.3880, "type": "shopping_street", "foot_traffic": 86, "rent_index": 84, "width_m": 20},
        {"id": "ber-st-alexanderplatz", "name": "Alexanderplatz", "catchment_id": "ber-mitte", "lat": 52.5220, "lon": 13.4130, "type": "transit_hub", "foot_traffic": 92, "rent_index": 78, "width_m": 40},
        {"id": "ber-st-orsanien", "name": "Oranienstraße", "catchment_id": "ber-kreuzberg", "lat": 52.4980, "lon": 13.4030, "type": "alternative_retail", "foot_traffic": 70, "rent_index": 55, "width_m": 12},
    ],
    "Madrid": [
        {"id": "mad-st-gran-via", "name": "Gran Vía", "catchment_id": "mad-gran-via", "lat": 40.4200, "lon": -3.7050, "type": "prime_avenue", "foot_traffic": 94, "rent_index": 88, "width_m": 25},
        {"id": "mad-st-serrano", "name": "Calle de Serrano", "catchment_id": "mad-salamanca", "lat": 40.4280, "lon": -3.6850, "type": "luxury_fashion", "foot_traffic": 70, "rent_index": 94, "width_m": 12},
        {"id": "mad-st-preciados", "name": "Calle Preciados", "catchment_id": "mad-sol", "lat": 40.4180, "lon": -3.7040, "type": "pedestrian_shopping", "foot_traffic": 92, "rent_index": 90, "width_m": 10},
        {"id": "mad-st-fuencarral", "name": "Calle de Fuencarral", "catchment_id": "mad-malasaña", "lat": 40.4260, "lon": -3.7050, "type": "trendy_retail", "foot_traffic": 78, "rent_index": 68, "width_m": 8},
    ],
}

CATCHMENT_TYPE_LABELS = {
    "historic_tourist": "Historic / Tourist",
    "trendy_lifestyle": "Trendy Lifestyle",
    "premium_shopping": "Premium Shopping",
    "luxury_boulevard": "Luxury Boulevard",
    "local_creative": "Local / Creative",
    "beach_tourist": "Beach / Tourist",
    "mall_modern": "Mall / Modern",
    "historic_fashion": "Historic Fashion",
    "premium_lifestyle": "Premium Lifestyle",
    "department_retail": "Department Retail",
    "tourist_artistic": "Tourist / Artistic",
    "young_urban": "Young Urban",
    "prime_high_street": "Prime High Street",
    "boutique_lifestyle": "Boutique Lifestyle",
    "luxury_fashion": "Luxury Fashion",
    "tourist_retail": "Tourist Retail",
    "fashion_district": "Fashion District",
    "mass_retail": "Mass Retail",
    "nightlife_lifestyle": "Nightlife / Lifestyle",
    "artistic_lifestyle": "Artistic Lifestyle",
    "tourist_hub": "Tourist Hub",
}

STREET_TYPE_LABELS = {
    "tourist_retail": "Tourist Retail",
    "boutique_street": "Boutique Street",
    "luxury_boulevard": "Luxury Boulevard",
    "tourist_boulevard": "Tourist Boulevard",
    "shopping_street": "Shopping Street",
    "local_commercial": "Local Commercial",
    "major_avenue": "Major Avenue",
    "luxury_fashion": "Luxury Fashion",
    "pedestrian_market": "Pedestrian Market",
    "boulevard_retail": "Boulevard Retail",
    "prime_high_street": "Prime High Street",
    "lifestyle_street": "Lifestyle Street",
    "fashion_district": "Fashion District",
    "pedestrian_plaza": "Pedestrian Plaza",
    "pedestrian_shopping": "Pedestrian Shopping",
    "mass_retail": "Mass Retail",
    "artistic_boutique": "Artistic Boutique",
    "premium_shopping": "Premium Shopping",
    "transit_hub": "Transit Hub",
    "alternative_retail": "Alternative Retail",
    "prime_avenue": "Prime Avenue",
    "trendy_retail": "Trendy Retail",
}


def _stable_rng(seed: str) -> float:
    h = hashlib.md5(seed.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _generate_catchments_for_city(city: str, lat: float, lon: float, tier: int) -> list[dict]:
    """Generate synthetic catchments for cities without hand-crafted data."""
    n = {1: 6, 2: 5, 3: 4}.get(tier, 4)
    types = ["prime_high_street", "premium_shopping", "trendy_lifestyle", "local_creative", "tourist_retail", "luxury_fashion"]
    names = ["City Centre", "North District", "South Quarter", "East Side", "West End", "Old Town"]
    catchments = []
    for i in range(n):
        rng = _stable_rng(f"{city}-catchment-{i}")
        offset_lat = (rng - 0.5) * 0.04
        offset_lon = (_stable_rng(f"{city}-c-{i}-lon") - 0.5) * 0.04
        clat, clon = lat + offset_lat, lon + offset_lon
        size = 0.012
        catchments.append({
            "id": f"{city.lower().replace(' ', '-')}-catch-{i}",
            "name": names[i % len(names)],
            "type": types[i % len(types)],
            "center": [clat, clon],
            "polygon": [
                [clat - size, clon - size],
                [clat - size, clon + size],
                [clat + size, clon + size],
                [clat + size, clon - size],
            ],
            "foot_traffic": round(50 + rng * 40 + tier * 5, 0),
            "tourist": round(20 + rng * 50, 0),
            "luxury": round(30 + rng * 50 + tier * 8, 0),
            "rent": round(40 + rng * 40 + tier * 5, 0),
            "income_factor": round(0.85 + rng * 0.3 + tier * 0.05, 2),
        })
    return catchments


def _generate_streets_for_city(city: str, catchments: list[dict]) -> list[dict]:
    streets = []
    for c in catchments:
        n_streets = 2 if c.get("has_meller_store") else 3
        for j in range(n_streets):
            rng = _stable_rng(f"{city}-{c['id']}-street-{j}")
            clat, clon = c["center"]
            slat = clat + (rng - 0.5) * 0.008
            slon = clon + (_stable_rng(f"{city}-{c['id']}-s-{j}") - 0.5) * 0.008
            streets.append({
                "id": f"{c['id']}-st-{j}",
                "name": f"{c['name']} — Retail Strip {j + 1}",
                "catchment_id": c["id"],
                "lat": slat,
                "lon": slon,
                "type": c["type"],
                "foot_traffic": round(c["foot_traffic"] * (0.9 + rng * 0.2), 0),
                "rent_index": round(c["rent"] * (0.85 + rng * 0.3), 0),
                "width_m": round(6 + rng * 20, 0),
            })
    return streets


def get_catchments(city: str, lat: float, lon: float, tier: int = 2) -> list[dict]:
    if city in CITY_CATCHMENTS:
        return CITY_CATCHMENTS[city]
    return _generate_catchments_for_city(city, lat, lon, tier)


def get_streets(city: str, lat: float = 0, lon: float = 0, tier: int = 2) -> list[dict]:
    if city in CITY_STREETS:
        return CITY_STREETS[city]
    catchments = get_catchments(city, lat, lon, tier)
    return _generate_streets_for_city(city, catchments)


def get_catchment_by_id(catchment_id: str, city: str, lat: float, lon: float, tier: int = 2) -> dict | None:
    for c in get_catchments(city, lat, lon, tier):
        if c["id"] == catchment_id:
            return c
    return None


def get_street_by_id(street_id: str, city: str, lat: float = 0, lon: float = 0, tier: int = 2) -> dict | None:
    for s in get_streets(city, lat, lon, tier):
        if s["id"] == street_id:
            return s
    return None
