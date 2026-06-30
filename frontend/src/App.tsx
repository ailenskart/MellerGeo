import { useCallback, useEffect, useMemo, useState } from 'react';
import ChatPanel from './components/ChatPanel';
import EuropeMap from './components/EuropeMap';
import MarketPanel from './components/MarketPanel';
import Sidebar from './components/Sidebar';
import {
  batchPredict,
  fetchCompetitors,
  fetchHealth,
  fetchMetrics,
  fetchSeasonality,
  fetchStores,
  predictCity,
  type CityLocation,
  type CompetitorAnalysis,
  type HealthStatus,
  type ModelMetrics,
  type RevenuePrediction,
  type SeasonalityAnalysis,
  type StoreLookupResult,
} from './api';

type Tab = 'analysis' | 'market' | 'chat';

export default function App() {
  const [cities, setCities] = useState<CityLocation[]>([]);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [selectedCity, setSelectedCity] = useState<CityLocation | null>(null);
  const [prediction, setPrediction] = useState<RevenuePrediction | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorAnalysis | null>(null);
  const [seasonality, setSeasonality] = useState<SeasonalityAnalysis | null>(null);
  const [stores, setStores] = useState<StoreLookupResult | null>(null);
  const [storeSize, setStoreSize] = useState(80);
  const [loading, setLoading] = useState(false);
  const [marketLoading, setMarketLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('analysis');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTier, setFilterTier] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([fetchHealth(), fetchMetrics()])
      .then(async ([healthData, metricsData]) => {
        setHealth(healthData);
        setMetrics(metricsData);
        const cityData = await batchPredict(80);
        setCities(cityData);
      })
      .catch((err) => setError(err.message));
  }, []);

  const filteredCities = useMemo(() => {
    let result = cities;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) => c.city.toLowerCase().includes(q) || c.country.toLowerCase().includes(q)
      );
    }
    if (filterTier) {
      result = result.filter((c) => c.city_tier === filterTier);
    }
    return result;
  }, [cities, searchQuery, filterTier]);

  const predictionsMap = useMemo(() => {
    const map: Record<string, RevenuePrediction> = {};
    for (const city of cities) {
      if (city.viability_score != null) {
        map[city.id] = {
          predicted_annual_revenue_eur: city.predicted_revenue_eur ?? 0,
          confidence_interval_low: 0,
          confidence_interval_high: 0,
          revenue_per_sqm: (city.predicted_revenue_eur ?? 0) / 80,
          viability_score: city.viability_score,
          viability_label: city.viability_score >= 75 ? 'Highly Recommended' : city.viability_score >= 55 ? 'Recommended' : city.viability_score >= 35 ? 'Moderate Potential' : 'Not Recommended',
          key_drivers: [],
          recommendation: '',
        };
      }
    }
    return map;
  }, [cities]);

  const loadMarketData = useCallback(async (cityId: string, size: number) => {
    setMarketLoading(true);
    try {
      const [comp, seas, storeData] = await Promise.all([
        fetchCompetitors(cityId),
        fetchSeasonality(cityId, size),
        fetchStores(cityId),
      ]);
      setCompetitors(comp);
      setSeasonality(seas);
      setStores(storeData);
    } catch {
      /* partial failure ok */
    } finally {
      setMarketLoading(false);
    }
  }, []);

  const analyzeCity = useCallback(async (city: CityLocation, size: number) => {
    setLoading(true);
    try {
      const pred = await predictCity(city.id, size);
      setPrediction(pred);
      await loadMarketData(city.id, size);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [loadMarketData]);

  const handleSelectCity = (city: CityLocation) => {
    setSelectedCity(city);
    analyzeCity(city, storeSize);
  };

  const handleStoreSizeChange = (size: number) => {
    setStoreSize(size);
    if (selectedCity) {
      analyzeCity(selectedCity, size);
    }
  };

  if (error && cities.length === 0) {
    return (
      <div className="app">
        <div className="empty-state" style={{ height: '100vh' }}>
          <h2>Unable to connect to API</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <h1>Meller</h1>
          <span>Geo Intelligence</span>
        </div>
        <div className="header-search">
          <input
            type="text"
            placeholder="Search cities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <select
            value={filterTier ?? ''}
            onChange={(e) => setFilterTier(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">All tiers</option>
            <option value="1">Tier 1</option>
            <option value="2">Tier 2</option>
            <option value="3">Tier 3</option>
          </select>
        </div>
        <div className="header-stats">
          <div className="stat">
            <div className="stat-label">Cities</div>
            <div className="stat-value">{health?.city_count ?? cities.length}</div>
          </div>
          {metrics && (
            <div className="stat">
              <div className="stat-label">Model Accuracy</div>
              <div className="stat-value">{(metrics.r2_score * 100).toFixed(1)}%</div>
            </div>
          )}
          <div className="stat">
            <div className="stat-label">AI Chat</div>
            <div className="stat-value">{health?.openai_enabled ? 'Live' : 'Local'}</div>
          </div>
        </div>
      </header>

      <main className="main main-3col">
        <div className="map-container">
          {filteredCities.length > 0 && (
            <EuropeMap
              cities={filteredCities}
              selectedCity={selectedCity}
              onSelectCity={handleSelectCity}
              predictions={predictionsMap}
            />
          )}
        </div>

        <div className="panel-center">
          <div className="tab-bar">
            <button className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>
              Analysis
            </button>
            <button className={activeTab === 'market' ? 'active' : ''} onClick={() => setActiveTab('market')}>
              Market
            </button>
            <button className={activeTab === 'chat' ? 'active' : ''} onClick={() => setActiveTab('chat')}>
              AI Chat
            </button>
          </div>

          {activeTab === 'analysis' && (
            <Sidebar
              city={selectedCity}
              prediction={prediction}
              metrics={metrics}
              storeSize={storeSize}
              onStoreSizeChange={handleStoreSizeChange}
              loading={loading}
            />
          )}
          {activeTab === 'market' && (
            <MarketPanel
              competitors={competitors}
              seasonality={seasonality}
              stores={stores}
              loading={marketLoading}
            />
          )}
          {activeTab === 'chat' && (
            <ChatPanel selectedCity={selectedCity} storeSize={storeSize} />
          )}
        </div>
      </main>
    </div>
  );
}
