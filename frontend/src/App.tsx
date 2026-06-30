import { useCallback, useEffect, useMemo, useState } from 'react';
import DataStatusBanner from './components/DataStatusBanner';
import ChatPanel from './components/ChatPanel';
import CityDetailMap from './components/CityDetailMap';
import EuropeMap from './components/EuropeMap';
import LocationPanel from './components/LocationPanel';
import MarketPanel from './components/MarketPanel';
import SocialPanel from './components/SocialPanel';
import SiteVisitPanel from './components/SiteVisitPanel';
import ComparePanel from './components/ComparePanel';
import ExpansionShortlist from './components/ExpansionShortlist';
import Sidebar from './components/Sidebar';
import {
  batchPredict,
  fetchCityIntelligence,
  fetchCityDetail,
  fetchCommercialProperties,
  fetchHealth,
  fetchMetrics,
  fetchSiteVisit,
  predictCity,
  type CatchmentArea,
  type CityDetailAnalysis,
  type CityLocation,
  type CommercialProperty,
  type CommercialPropertySearch,
  type CompetitorAnalysis,
  type HealthStatus,
  type ModelMetrics,
  type RevenuePrediction,
  type SeasonalityAnalysis,
  type SocialIntelligenceReport,
  type SiteVisitContext,
  type StoreLookupResult,
  type StreetLocation,
} from './api';

type Tab = 'analysis' | 'locations' | 'market' | 'social' | 'visit' | 'compare' | 'chat'

const SHORTLIST_KEY = 'meller-expansion-shortlist';
type MapMode = 'europe' | 'city';

export default function App() {
  const [cities, setCities] = useState<CityLocation[]>([]);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [selectedCity, setSelectedCity] = useState<CityLocation | null>(null);
  const [prediction, setPrediction] = useState<RevenuePrediction | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorAnalysis | null>(null);
  const [seasonality, setSeasonality] = useState<SeasonalityAnalysis | null>(null);
  const [stores, setStores] = useState<StoreLookupResult | null>(null);
  const [socialReport, setSocialReport] = useState<SocialIntelligenceReport | null>(null);
  const [cityDetail, setCityDetail] = useState<CityDetailAnalysis | null>(null);
  const [commercialProperties, setCommercialProperties] = useState<CommercialPropertySearch | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<CommercialProperty | null>(null);
  const [propertiesLoading, setPropertiesLoading] = useState(false);
  const [selectedCatchment, setSelectedCatchment] = useState<CatchmentArea | null>(null);
  const [selectedStreet, setSelectedStreet] = useState<StreetLocation | null>(null);
  const [mapMode, setMapMode] = useState<MapMode>('europe');
  const [storeSize, setStoreSize] = useState(80);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [marketLoading, setMarketLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState(false);
  const [dataWarning, setDataWarning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('analysis');
  const [siteVisit, setSiteVisit] = useState<SiteVisitContext | null>(null);
  const [siteVisitLoading, setSiteVisitLoading] = useState(false);
  const [shortlistIds, setShortlistIds] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(SHORTLIST_KEY) || '[]');
    } catch {
      return [];
    }
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [filterTier, setFilterTier] = useState<number | null>(null);

  const shortlist = useMemo(
    () => shortlistIds.map((id) => cities.find((c) => c.id === id)).filter(Boolean) as CityLocation[],
    [shortlistIds, cities],
  );

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

  const loadProperties = useCallback(async (
    cityId: string,
    size: number,
    opts?: { catchmentId?: string; streetId?: string },
  ) => {
    setPropertiesLoading(true);
    try {
      const data = await fetchCommercialProperties(cityId, size, opts);
      setCommercialProperties(data);
    } catch {
      setCommercialProperties(null);
    } finally {
      setPropertiesLoading(false);
    }
  }, []);

  const loadCityDetail = useCallback(async (cityId: string, size: number) => {
    setDetailLoading(true);
    try {
      const detail = await fetchCityDetail(cityId, size);
      setCityDetail(detail);
      setSelectedCatchment(null);
      setSelectedStreet(null);
    } catch {
      setCityDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadIntelligence = useCallback(async (
    cityId: string,
    size: number,
    opts?: { catchmentId?: string; streetId?: string },
  ) => {
    setMarketLoading(true);
    setSocialLoading(true);
    setDataWarning(null);
    try {
      const bundle = await fetchCityIntelligence(cityId, size, opts);
      setCompetitors(bundle.competitors);
      setSeasonality(bundle.seasonality);
      setStores(bundle.stores);
      setSocialReport(bundle.social);

      const warnings = bundle.competitors.data_quality?.warnings as string[] | undefined;
      if (warnings?.length && !bundle.google_status?.live) {
        setDataWarning(null);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load intelligence data';
      setDataWarning(msg);
      setCompetitors(null);
      setSeasonality(null);
      setStores(null);
      setSocialReport(null);
    } finally {
      setMarketLoading(false);
      setSocialLoading(false);
    }
  }, []);

  const loadSocialData = useCallback(async (
    cityId: string,
    catchmentId?: string | null,
    streetId?: string | null,
    size: number = storeSize,
  ) => {
    await loadIntelligence(cityId, size, {
      catchmentId: catchmentId ?? undefined,
      streetId: streetId ?? undefined,
    });
  }, [loadIntelligence, storeSize]);

  const loadMarketData = useCallback(async (cityId: string, size: number) => {
    await loadIntelligence(cityId, size);
  }, [loadIntelligence]);

  const loadSiteVisit = useCallback(async (
    cityId: string,
    size: number,
    opts?: { catchmentId?: string; streetId?: string },
  ) => {
    setSiteVisitLoading(true);
    try {
      const data = await fetchSiteVisit(cityId, size, opts);
      setSiteVisit(data);
    } catch {
      setSiteVisit(null);
    } finally {
      setSiteVisitLoading(false);
    }
  }, []);

  const toggleShortlist = useCallback((cityId: string) => {
    setShortlistIds((prev) => {
      const next = prev.includes(cityId) ? prev.filter((id) => id !== cityId) : [...prev, cityId];
      localStorage.setItem(SHORTLIST_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const clearShortlist = useCallback(() => {
    setShortlistIds([]);
    localStorage.removeItem(SHORTLIST_KEY);
  }, []);

  const analyzeCity = useCallback(async (city: CityLocation, size: number) => {
    setLoading(true);
    setMapMode('city');
    setActiveTab('locations');
    try {
      const pred = await predictCity(city.id, size);
      setPrediction(pred);
      await Promise.all([
        loadMarketData(city.id, size),
        loadCityDetail(city.id, size),
        loadProperties(city.id, size),
        loadSiteVisit(city.id, size),
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [loadMarketData, loadCityDetail, loadProperties, loadSiteVisit]);

  const handleSelectCatchment = (c: CatchmentArea | null) => {
    setSelectedCatchment(c);
    setSelectedStreet(null);
    setSelectedProperty(null);
    if (selectedCity && c) {
      loadSocialData(selectedCity.id, c.id);
      loadProperties(selectedCity.id, storeSize, { catchmentId: c.id });
      loadSiteVisit(selectedCity.id, storeSize, { catchmentId: c.id });
    } else if (selectedCity) {
      loadSocialData(selectedCity.id);
      loadProperties(selectedCity.id, storeSize);
      loadSiteVisit(selectedCity.id, storeSize);
    }
  };

  const handleSelectStreet = (s: StreetLocation | null) => {
    setSelectedStreet(s);
    setSelectedProperty(null);
    if (selectedCity && s) {
      loadSocialData(selectedCity.id, s.catchment_id ?? undefined, s.id);
      loadProperties(selectedCity.id, storeSize, {
        catchmentId: s.catchment_id ?? undefined,
        streetId: s.id,
      });
      loadSiteVisit(selectedCity.id, storeSize, {
        catchmentId: s.catchment_id ?? undefined,
        streetId: s.id,
      });
      setActiveTab('visit');
    }
  };

  const handleSelectProperty = (p: CommercialProperty) => {
    setSelectedProperty(p);
  };

  const handleSelectCity = (city: CityLocation) => {
    setSelectedCity(city);
    analyzeCity(city, storeSize);
  };

  const handleBackToEurope = () => {
    setMapMode('europe');
    setSelectedCity(null);
    setCityDetail(null);
    setSelectedCatchment(null);
    setSelectedStreet(null);
    setSelectedProperty(null);
    setCommercialProperties(null);
    setSocialReport(null);
    setDataWarning(null);
    setPrediction(null);
    setActiveTab('analysis');
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
        <a className="logo" href="https://mellerbrand.com" target="_blank" rel="noopener noreferrer">
          <span className="logo-wordmark">MELLER</span>
          <span className="logo-divider" />
          <span className="logo-sub">Geo Intelligence</span>
        </a>
        <div className="header-search">
          {mapMode === 'europe' ? (
            <>
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
            </>
          ) : (
            <button type="button" className="back-btn" onClick={handleBackToEurope}>
              ← Back to Europe
            </button>
          )}
        </div>
        <div className="header-stats">
          <div className="stat">
            <div className="stat-label">{mapMode === 'city' ? 'City' : 'Cities'}</div>
            <div className="stat-value">
              {mapMode === 'city' && selectedCity ? selectedCity.city : (health?.city_count ?? cities.length)}
            </div>
          </div>
          {mapMode === 'city' && cityDetail && (
            <div className="stat">
              <div className="stat-label">Catchments</div>
              <div className="stat-value">{cityDetail.catchments.length}</div>
            </div>
          )}
          {metrics && mapMode === 'europe' && (
            <div className="stat">
              <div className="stat-label">Model Accuracy</div>
              <div className="stat-value">{(metrics.r2_score * 100).toFixed(1)}%</div>
            </div>
          )}
        </div>
      </header>

      <DataStatusBanner health={health} dataWarning={dataWarning} />

      <main className="main main-3col">
        <div className="map-container">
          {mapMode === 'europe' && filteredCities.length > 0 && (
            <EuropeMap
              cities={filteredCities}
              selectedCity={selectedCity}
              onSelectCity={handleSelectCity}
              predictions={predictionsMap}
            />
          )}
          {mapMode === 'city' && selectedCity && cityDetail && (
            <CityDetailMap
              city={selectedCity}
              catchments={cityDetail.catchments}
              streets={cityDetail.streets}
              properties={commercialProperties?.listings ?? []}
              selectedCatchment={selectedCatchment}
              selectedStreet={selectedStreet}
              selectedProperty={selectedProperty}
              onSelectCatchment={handleSelectCatchment}
              onSelectStreet={handleSelectStreet}
              onSelectProperty={handleSelectProperty}
            />
          )}
          {mapMode === 'city' && detailLoading && (
            <div className="map-loading">Loading city detail...</div>
          )}
        </div>

        <div className="panel-center">
          <div className="tab-bar">
            <button className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>
              Analysis
            </button>
            <button
              className={activeTab === 'locations' ? 'active' : ''}
              onClick={() => setActiveTab('locations')}
              disabled={!selectedCity}
            >
              Locations
            </button>
            <button className={activeTab === 'market' ? 'active' : ''} onClick={() => setActiveTab('market')}>
              Market
            </button>
            <button
              className={activeTab === 'social' ? 'active' : ''}
              onClick={() => setActiveTab('social')}
              disabled={!selectedCity}
            >
              Social
              {selectedCity && socialReport && !socialLoading && (
                <span className="tab-badge" title="Social data loaded">●</span>
              )}
            </button>
            <button
              className={activeTab === 'visit' ? 'active' : ''}
              onClick={() => setActiveTab('visit')}
              disabled={!selectedCity}
            >
              Site visit
            </button>
            <button className={activeTab === 'compare' ? 'active' : ''} onClick={() => setActiveTab('compare')}>
              Compare
            </button>
            <button className={activeTab === 'chat' ? 'active' : ''} onClick={() => setActiveTab('chat')}>
              AI Chat
            </button>
          </div>

          {activeTab === 'analysis' && (
            <>
              <ExpansionShortlist
                shortlist={shortlist}
                onRemove={toggleShortlist}
                onClear={clearShortlist}
                onSelect={handleSelectCity}
                onCompare={() => setActiveTab('compare')}
              />
              <Sidebar
                city={selectedCity}
                prediction={prediction}
                metrics={metrics}
                storeSize={storeSize}
                onStoreSizeChange={handleStoreSizeChange}
                loading={loading}
                inShortlist={selectedCity ? shortlistIds.includes(selectedCity.id) : false}
                onToggleShortlist={selectedCity ? () => toggleShortlist(selectedCity.id) : undefined}
              />
            </>
          )}
          {activeTab === 'locations' && selectedCity && (
            <LocationPanel
              city={selectedCity}
              catchments={cityDetail?.catchments ?? []}
              streets={cityDetail?.streets ?? []}
              selectedCatchment={selectedCatchment}
              selectedStreet={selectedStreet}
              onSelectCatchment={handleSelectCatchment}
              onSelectStreet={handleSelectStreet}
              onOpenSocial={() => setActiveTab('social')}
              properties={commercialProperties}
              propertiesLoading={propertiesLoading}
              selectedPropertyId={selectedProperty?.id ?? null}
              onSelectProperty={handleSelectProperty}
              loading={detailLoading}
            />
          )}
          {activeTab === 'social' && (
            <SocialPanel report={socialReport} loading={socialLoading} />
          )}
          {activeTab === 'visit' && (
            <SiteVisitPanel siteVisit={siteVisit} loading={siteVisitLoading} />
          )}
          {activeTab === 'compare' && (
            <ComparePanel
              cities={cities}
              storeSize={storeSize}
              selectedCity={selectedCity}
              shortlist={shortlist}
            />
          )}
          {activeTab === 'market' && (
            <MarketPanel
              competitors={competitors}
              seasonality={seasonality}
              stores={stores}
              loading={marketLoading}
              dataWarning={dataWarning}
            />
          )}
          {activeTab === 'chat' && (
            <ChatPanel selectedCity={selectedCity} storeSize={storeSize} />
          )}
        </div>
      </main>

      <footer className="footer">
        <div>
          <a href="https://mellerbrand.com" target="_blank" rel="noopener noreferrer">mellerbrand.com</a>
          {' · '}
          <a href="https://mellerbrand.com/pages/our-stores" target="_blank" rel="noopener noreferrer">Our Stores</a>
        </div>
        <div className="footer-trust">
          <span><strong>3M+</strong> customers</span>
          <span>Trustpilot <strong>4.4</strong></span>
          <span>Google <strong>4.5</strong></span>
        </div>
      </footer>
    </div>
  );
}
