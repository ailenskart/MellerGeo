export interface GeoParameters {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  population: number;
  population_density: number;
  gdp_per_capita: number;
  avg_household_income: number;
  foot_traffic_index: number;
  tourist_index: number;
  fashion_competitor_density: number;
  luxury_retail_proximity: number;
  public_transport_score: number;
  retail_rent_index: number;
  median_age: number;
  ecommerce_penetration: number;
  mall_vs_street: number;
  store_size_sqm: number;
  city_tier: number;
}

export interface RevenuePrediction {
  predicted_annual_revenue_eur: number;
  confidence_interval_low: number;
  confidence_interval_high: number;
  revenue_per_sqm: number;
  viability_score: number;
  viability_label: string;
  key_drivers: { factor: string; importance: number; value: number | string }[];
  recommendation: string;
}

export interface CityLocation {
  id: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  population: number;
  gdp_per_capita: number;
  foot_traffic_index: number;
  city_tier: number;
  has_existing_store: boolean;
  actual_revenue_eur: number | null;
}

export interface ModelMetrics {
  r2_score: number;
  mae_eur: number;
  rmse_eur: number;
  training_samples: number;
  feature_importance: { feature: string; importance: number }[];
}

const API_BASE = '/api';

export async function fetchCities(): Promise<CityLocation[]> {
  const res = await fetch(`${API_BASE}/cities`);
  if (!res.ok) throw new Error('Failed to fetch cities');
  return res.json();
}

export async function fetchMetrics(): Promise<ModelMetrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function predictCity(cityId: string, storeSize: number): Promise<RevenuePrediction> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/predict?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Prediction failed');
  return res.json();
}

export async function predictCustom(params: GeoParameters): Promise<RevenuePrediction> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Prediction failed');
  return res.json();
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-EU', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-EU').format(value);
}
