import { useCallback, useEffect, useState } from 'react';
import EuropeMap from './components/EuropeMap';
import Sidebar from './components/Sidebar';
import {
  fetchCities,
  fetchMetrics,
  predictCity,
  type CityLocation,
  type ModelMetrics,
  type RevenuePrediction,
} from './api';

export default function App() {
  const [cities, setCities] = useState<CityLocation[]>([]);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [selectedCity, setSelectedCity] = useState<CityLocation | null>(null);
  const [prediction, setPrediction] = useState<RevenuePrediction | null>(null);
  const [predictions, setPredictions] = useState<Record<string, RevenuePrediction>>({});
  const [storeSize, setStoreSize] = useState(80);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchCities(), fetchMetrics()])
      .then(([cityData, metricsData]) => {
        setCities(cityData);
        setMetrics(metricsData);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (cities.length === 0) return;

    const loadPredictions = async () => {
      const results: Record<string, RevenuePrediction> = {};
      await Promise.all(
        cities.map(async (city) => {
          try {
            const pred = await predictCity(city.id, 80);
            results[city.id] = pred;
          } catch {
            /* skip failed predictions */
          }
        })
      );
      setPredictions(results);
    };
    loadPredictions();
  }, [cities]);

  const analyzeCity = useCallback(async (city: CityLocation, size: number) => {
    setLoading(true);
    try {
      const pred = await predictCity(city.id, size);
      setPrediction(pred);
      setPredictions((prev) => ({ ...prev, [city.id]: pred }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, []);

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
          <p style={{ marginTop: '1rem', fontSize: '0.85rem' }}>
            Start the backend: <code>cd backend && uvicorn app.main:app --reload</code>
          </p>
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
        <div className="header-stats">
          <div className="stat">
            <div className="stat-label">Cities Analyzed</div>
            <div className="stat-value">{cities.length}</div>
          </div>
          {metrics && (
            <div className="stat">
              <div className="stat-label">Model Accuracy</div>
              <div className="stat-value">{(metrics.r2_score * 100).toFixed(1)}%</div>
            </div>
          )}
          <div className="stat">
            <div className="stat-label">Coverage</div>
            <div className="stat-value">Europe</div>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="map-container">
          {cities.length > 0 && (
            <EuropeMap
              cities={cities}
              selectedCity={selectedCity}
              onSelectCity={handleSelectCity}
              predictions={predictions}
            />
          )}
        </div>
        <Sidebar
          city={selectedCity}
          prediction={prediction}
          metrics={metrics}
          storeSize={storeSize}
          onStoreSizeChange={handleStoreSizeChange}
          loading={loading}
        />
      </main>
    </div>
  );
}
