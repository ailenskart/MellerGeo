import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { CityLocation, ModelMetrics, RevenuePrediction } from '../api';
import { formatCurrency, formatNumber } from '../api';

interface Props {
  city: CityLocation | null;
  prediction: RevenuePrediction | null;
  metrics: ModelMetrics | null;
  storeSize: number;
  onStoreSizeChange: (size: number) => void;
  loading: boolean;
}

function getViabilityClass(score: number): string {
  if (score >= 55) return 'high';
  if (score >= 35) return 'medium';
  return 'low';
}

export default function Sidebar({
  city,
  prediction,
  metrics,
  storeSize,
  onStoreSizeChange,
  loading,
}: Props) {
  if (!city) {
    return (
      <aside className="sidebar">
        <div className="empty-state">
          <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.5rem', color: 'var(--text-secondary)' }}>
            Select a location
          </h2>
          <p>Click any city on the map to analyze its revenue potential for a new Meller store.</p>
        </div>
        {metrics && (
          <div className="sidebar-section">
            <h2>Model Performance</h2>
            <div className="city-meta">
              <span className="badge">R² {metrics.r2_score}</span>
              <span className="badge">MAE {formatCurrency(metrics.mae_eur)}</span>
              <span className="badge">{metrics.training_samples} samples</span>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metrics.feature_importance.slice(0, 6)} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis
                    type="category"
                    dataKey="feature"
                    width={110}
                    tick={{ fill: '#999', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#fff',
                      border: '1px solid #E5E5E5',
                      borderRadius: 0,
                      color: '#111',
                    }}
                  />
                  <Bar dataKey="importance" fill="#FF6723" radius={[0, 2, 2, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-section city-info">
        <h2>Location Analysis</h2>
        <h3>{city.city}</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{city.country}</p>
        <div className="city-meta">
          <span className={`badge tier-${city.city_tier}`}>Tier {city.city_tier}</span>
          <span className="badge">{formatNumber(city.population)} pop.</span>
          <span className="badge">GDP €{formatNumber(city.gdp_per_capita)}</span>
          {city.has_existing_store && <span className="badge existing">MELLER Store</span>}
        </div>
      </div>

      <div className="sidebar-section">
        <h2>Store Configuration</h2>
        <div className="slider-group">
          <label>
            <span>Store Size</span>
            <span>{storeSize} m²</span>
          </label>
          <input
            type="range"
            min={40}
            max={200}
            step={10}
            value={storeSize}
            onChange={(e) => onStoreSizeChange(Number(e.target.value))}
          />
        </div>
      </div>

      {loading ? (
        <div className="loading">Analyzing location...</div>
      ) : prediction ? (
        <>
          <div className="sidebar-section">
            <h2>Revenue Forecast</h2>
            <div className="revenue-card">
              <div className="revenue-main">
                {formatCurrency(prediction.predicted_annual_revenue_eur)}
              </div>
              <div className="revenue-range">
                Range: {formatCurrency(prediction.confidence_interval_low)} – {formatCurrency(prediction.confidence_interval_high)}
              </div>
              <div className="revenue-per-sqm">
                {formatCurrency(prediction.revenue_per_sqm)} / m² annually
              </div>
              <div className="viability">
                <div className={`viability-score ${getViabilityClass(prediction.viability_score)}`}>
                  {prediction.viability_score}
                </div>
                <div>
                  <div className="viability-label">{prediction.viability_label}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Viability Score</div>
                </div>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h2>Recommendation</h2>
            <p className="recommendation">{prediction.recommendation}</p>
          </div>

          <div className="sidebar-section">
            <h2>Key Revenue Drivers</h2>
            <ul className="drivers-list">
              {prediction.key_drivers.map((driver) => (
                <li key={driver.factor}>
                  <span style={{ minWidth: 120 }}>{driver.factor}</span>
                  <div className="driver-bar">
                    <div
                      className="driver-bar-fill"
                      style={{ width: `${(driver.importance / 0.3) * 100}%` }}
                    />
                  </div>
                  <span style={{ color: 'var(--text-muted)', minWidth: 50, textAlign: 'right' }}>
                    {typeof driver.value === 'number' ? driver.value.toLocaleString() : driver.value}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      ) : null}
    </aside>
  );
}
