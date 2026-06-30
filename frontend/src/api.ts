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
  tourist_index: number;
  city_tier: number;
  has_existing_store: boolean;
  actual_revenue_eur: number | null;
  predicted_revenue_eur?: number | null;
  viability_score?: number | null;
}

export interface ModelMetrics {
  r2_score: number;
  mae_eur: number;
  rmse_eur: number;
  training_samples: number;
  feature_importance: { feature: string; importance: number }[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  message: ChatMessage;
  context_used: string[];
  source: string;
}

export interface CompetitorStore {
  brand: string;
  tier: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  rating: number;
  estimated_annual_revenue_eur: number;
  store_type: string;
}

export interface CompetitorAnalysis {
  city: string;
  country: string;
  total_competitors: number;
  brands_present: string[];
  market_saturation_score: number;
  luxury_competitor_count: number;
  direct_eyewear_stores: number;
  nearest_competitors: CompetitorStore[];
  market_assessment: string;
  meller_opportunity_score: number;
  ai_verified?: boolean;
  verification_confidence?: number | null;
  data_quality?: Record<string, unknown>;
}

export interface MonthlyRevenue {
  month: number;
  month_name: string;
  revenue_eur: number;
  seasonal_index: number;
  season: string;
}

export interface SeasonalityAnalysis {
  city: string;
  annual_revenue_eur: number;
  monthly_revenue: MonthlyRevenue[];
  market_insights: Record<string, string | number | boolean>;
}

export interface PlaceResult {
  place_id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  rating: number | null;
  user_ratings_total: number;
  estimated_size_sqm: number;
}

export interface StoreLookupResult {
  meller_stores: PlaceResult[];
  nearby_competitors: PlaceResult[];
  google_maps_enabled: boolean;
  ai_verified?: boolean;
  data_quality?: Record<string, unknown>;
}

export interface CommercialProperty {
  id: string;
  title: string;
  address: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  broker: string;
  broker_id: string;
  broker_portal: string;
  listing_url: string;
  property_type: string;
  property_type_label: string;
  size_sqm: number;
  rent_eur_monthly: number;
  rent_eur_sqm_year: number;
  availability: string;
  availability_label: string;
  catchment_id: string | null;
  street_id: string | null;
  street_name: string | null;
  catchment_name: string | null;
  description: string;
  meller_fit_score: number;
  distance_km: number;
  data_source: string;
  contact: string;
}

export interface CommercialPropertySearch {
  city: string;
  country: string;
  total_listings: number;
  available_count: number;
  brokers: string[];
  broker_directory: { id: string; name: string; listing_portal: string }[];
  listings: CommercialProperty[];
  top_pick: CommercialProperty | null;
  google_live: boolean;
  data_sources: Record<string, number>;
  summary: string;
}

export interface CityDetailAnalysis {
  city: string;
  country: string;
  city_id: string;
  catchments: CatchmentArea[];
  streets: StreetLocation[];
  top_catchment: CatchmentArea | null;
  top_street: StreetLocation | null;
}

export interface CatchmentArea {
  id: string;
  name: string;
  type: string;
  type_label: string;
  center: { latitude: number; longitude: number };
  polygon: number[][];
  foot_traffic_index: number;
  tourist_index: number;
  luxury_retail_score: number;
  retail_rent_index: number;
  has_meller_store: boolean;
  predicted_annual_revenue_eur: number;
  viability_score: number;
  viability_label: string;
  revenue_per_sqm: number;
  recommendation: string;
  street_count: number;
}

export interface StreetLocation {
  id: string;
  name: string;
  catchment_id: string | null;
  catchment_name: string | null;
  type: string;
  type_label: string;
  latitude: number;
  longitude: number;
  foot_traffic_index: number;
  retail_rent_index: number;
  street_width_m: number | null;
  has_meller_store: boolean;
  predicted_annual_revenue_eur: number;
  viability_score: number;
  viability_label: string;
  revenue_per_sqm: number;
  confidence_interval_low: number | null;
  confidence_interval_high: number | null;
  recommendation: string;
  key_drivers: { factor: string; importance: number; value: number | string }[];
}

export interface SocialReview {
  author: string;
  rating?: number | null;
  text: string;
  time: string;
  source: string;
  likes?: number | null;
  comments?: number | null;
  sentiment?: string | null;
}

export interface ShoppingDestination {
  name: string;
  social_buzz_score: number;
  google_rating: number;
  foot_traffic_estimate: number;
  instagram_mentions: number;
  why_popular: string;
  best_for: string;
}

export interface PlatformSocialData {
  platform: string;
  sentiment_score: number;
  mention_volume_monthly?: number | null;
  average_rating?: number | null;
  total_reviews?: number | null;
  review_count_analyzed?: number | null;
  engagement_rate?: number | null;
  top_posts?: Record<string, unknown>[];
  top_rated_nearby?: Record<string, unknown>[];
  reviews?: SocialReview[];
  hashtag_volume?: Record<string, number>;
  trending_topics?: string[];
  shopping_tags?: string[];
  influencer_visits_monthly?: number | null;
  shopping_intent_mentions?: number | null;
}

export interface SocialIntelligenceReport {
  location: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  overall_sentiment_score: number;
  overall_sentiment_label: string;
  shopping_intent_score: number;
  google: PlatformSocialData;
  instagram: PlatformSocialData;
  twitter: PlatformSocialData;
  shopping_destinations: ShoppingDestination[];
  top_positive_themes: string[];
  top_negative_themes: string[];
  where_people_shop: string[];
  data_sources: Record<string, boolean>;
  summary: string;
  ai_verified?: boolean;
  review_insights?: string[];
  data_quality?: Record<string, unknown>;
}

export interface HealthStatus {
  status: string;
  model_loaded: boolean;
  city_count: number;
  openai_enabled: boolean;
  google_maps_enabled: boolean;
  google_maps_live?: boolean;
  osm_live?: boolean;
  maps_live?: boolean;
  maps_live_source?: string | null;
  google_api_error?: string | null;
  google_enable_url?: string | null;
  google_fix_instructions?: string | null;
  ai_verification_enabled?: boolean;
}

export interface CityIntelligenceBundle {
  competitors: CompetitorAnalysis;
  stores: StoreLookupResult;
  social: SocialIntelligenceReport;
  seasonality: SeasonalityAnalysis;
  google_status?: Record<string, unknown>;
}

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchCities(params?: { country?: string; tier?: number; search?: string }): Promise<CityLocation[]> {
  const qs = new URLSearchParams();
  if (params?.country) qs.set('country', params.country);
  if (params?.tier) qs.set('tier', String(params.tier));
  if (params?.search) qs.set('search', params.search);
  const res = await fetch(`${API_BASE}/cities?${qs}`);
  if (!res.ok) throw new Error('Failed to fetch cities');
  return res.json();
}

export async function fetchMetrics(): Promise<ModelMetrics> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
}

export async function batchPredict(storeSize: number = 80): Promise<CityLocation[]> {
  const res = await fetch(`${API_BASE}/cities/batch-predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ store_size_sqm: storeSize }),
  });
  if (!res.ok) throw new Error('Batch prediction failed');
  return res.json();
}

export async function predictCity(cityId: string, storeSize: number): Promise<RevenuePrediction> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/predict?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Prediction failed');
  return res.json();
}

export async function fetchCommercialProperties(
  cityId: string,
  storeSize: number = 80,
  params?: { catchmentId?: string; streetId?: string },
): Promise<CommercialPropertySearch> {
  const qs = new URLSearchParams({ store_size_sqm: String(storeSize) });
  if (params?.catchmentId) qs.set('catchment_id', params.catchmentId);
  if (params?.streetId) qs.set('street_id', params.streetId);
  const res = await fetch(`${API_BASE}/cities/${cityId}/properties?${qs}`);
  if (!res.ok) throw new Error('Commercial property search failed');
  return res.json();
}

export async function fetchCityIntelligence(
  cityId: string,
  storeSize: number = 80,
  params?: { catchmentId?: string; streetId?: string },
): Promise<CityIntelligenceBundle> {
  const qs = new URLSearchParams({ store_size_sqm: String(storeSize) });
  if (params?.catchmentId) qs.set('catchment_id', params.catchmentId);
  if (params?.streetId) qs.set('street_id', params.streetId);
  const res = await fetch(`${API_BASE}/cities/${cityId}/intelligence?${qs}`);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Intelligence fetch failed');
  }
  return res.json();
}

export async function fetchCompetitors(cityId: string, storeSize: number = 80): Promise<CompetitorAnalysis> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/competitors?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Competitor analysis failed');
  return res.json();
}

export async function fetchSeasonality(cityId: string, storeSize: number): Promise<SeasonalityAnalysis> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/seasonality?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Seasonality analysis failed');
  return res.json();
}

export async function fetchStores(cityId: string, storeSize: number = 80): Promise<StoreLookupResult> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/stores?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Store lookup failed');
  return res.json();
}

export async function fetchCityDetail(cityId: string, storeSize: number = 80): Promise<CityDetailAnalysis> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/detail?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('City detail failed');
  return res.json();
}

export async function fetchCityCatchments(cityId: string, storeSize: number = 80): Promise<CatchmentArea[]> {
  const res = await fetch(`${API_BASE}/cities/${cityId}/catchments?store_size_sqm=${storeSize}`);
  if (!res.ok) throw new Error('Catchment analysis failed');
  return res.json();
}

export async function fetchCityStreets(
  cityId: string,
  storeSize: number = 80,
  catchmentId?: string,
): Promise<StreetLocation[]> {
  const qs = new URLSearchParams({ store_size_sqm: String(storeSize) });
  if (catchmentId) qs.set('catchment_id', catchmentId);
  const res = await fetch(`${API_BASE}/cities/${cityId}/streets?${qs}`);
  if (!res.ok) throw new Error('Street analysis failed');
  return res.json();
}

export async function fetchSocialIntelligence(
  cityId: string,
  params?: { catchmentId?: string; streetId?: string },
): Promise<SocialIntelligenceReport> {
  const qs = new URLSearchParams();
  if (params?.catchmentId) qs.set('catchment_id', params.catchmentId);
  if (params?.streetId) qs.set('street_id', params.streetId);
  const res = await fetch(`${API_BASE}/cities/${cityId}/social?${qs}`);
  if (!res.ok) throw new Error('Social intelligence failed');
  return res.json();
}

export async function sendChat(
  messages: ChatMessage[],
  cityId?: string | null,
  storeSize?: number,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      city_id: cityId ?? null,
      store_size_sqm: storeSize ?? 80,
    }),
  });
  if (!res.ok) throw new Error('Chat failed');
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
