import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CompetitorAnalysis, SeasonalityAnalysis, StoreLookupResult } from '../api';
import { formatCurrency } from '../api';

interface Props {
  competitors: CompetitorAnalysis | null;
  seasonality: SeasonalityAnalysis | null;
  stores: StoreLookupResult | null;
  loading: boolean;
  dataWarning?: string | null;
}

export default function MarketPanel({ competitors, seasonality, stores, loading, dataWarning }: Props) {
  if (loading) {
    return <div className="loading">Loading and verifying market intelligence…</div>;
  }

  if (!competitors && !seasonality) {
    return (
      <div className="empty-state" style={{ padding: '2rem 1rem' }}>
        <p>{dataWarning || 'Select a city to see competitor analysis, seasonality, and store data.'}</p>
      </div>
    );
  }

  return (
    <div className="market-panel">
      {competitors && (
        <section className="market-section">
          <h3>
            Competitor Landscape
            {competitors.ai_verified && (
              <span className="ai-badge" title="Cross-checked by OpenAI against Google Maps">AI Verified</span>
            )}
          </h3>
          <div className="market-stats">
            <div className="market-stat">
              <span className="market-stat-value">{competitors.total_competitors}</span>
              <span className="market-stat-label">Competitors</span>
            </div>
            <div className="market-stat">
              <span className="market-stat-value">{competitors.meller_opportunity_score}</span>
              <span className="market-stat-label">Opportunity</span>
            </div>
            <div className="market-stat">
              <span className="market-stat-value">{competitors.market_saturation_score}%</span>
              <span className="market-stat-label">Saturation</span>
            </div>
          </div>
          <p className="market-assessment">{competitors.market_assessment}</p>
          {competitors.verification_confidence != null && competitors.ai_verified && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              Verification confidence: {competitors.verification_confidence}%
            </p>
          )}
          <div className="brand-tags">
            {competitors.brands_present.map((b) => (
              <span key={b} className={`brand-tag ${b === 'Meller' ? 'meller' : ''}`}>{b}</span>
            ))}
          </div>
          <ul className="competitor-list">
            {competitors.nearest_competitors.slice(0, 5).map((c, i) => (
              <li key={i}>
                <span className="comp-brand">{c.brand}</span>
                <span className="comp-tier">{c.tier}</span>
                <span className="comp-dist">{c.distance_km} km</span>
                <span className="comp-rev">{formatCurrency(c.estimated_annual_revenue_eur)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {seasonality && (
        <section className="market-section">
          <h3>Seasonal Revenue</h3>
          <div className="season-insights">
            <span className="badge">Peak: {seasonality.market_insights.peak_season as string}</span>
            <span className="badge">Low: {seasonality.market_insights.low_season as string}</span>
            {seasonality.market_insights.is_tourist_destination && (
              <span className="badge existing">Tourist Hub</span>
            )}
          </div>
          <div className="chart-container" style={{ height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={seasonality.monthly_revenue}>
                <XAxis
                  dataKey="month_name"
                  tick={{ fill: '#71717a', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  interval={2}
                />
                <YAxis hide />
                <Tooltip
                  contentStyle={{
                    background: '#1a1a1e',
                    border: '1px solid #2a2a32',
                    borderRadius: 8,
                    color: '#f4f4f5',
                    fontSize: 12,
                  }}
                  formatter={(value: number) => [formatCurrency(value), 'Revenue']}
                />
                <Area
                  type="monotone"
                  dataKey="revenue_eur"
                  stroke="#FF6723"
                  fill="url(#seasonGradient)"
                  strokeWidth={2}
                />
                <defs>
                  <linearGradient id="seasonGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#FF6723" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#FF6723" stopOpacity={0} />
                  </linearGradient>
                </defs>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}

      {stores && (
        <section className="market-section">
          <h3>MELLER Stores</h3>
          {stores.meller_stores.length > 0 ? (
            <ul className="store-list">
              {stores.meller_stores.map((s) => (
                <li key={s.place_id}>
                  <strong>{s.name}</strong>
                  <span>{s.address}</span>
                  <span>~{s.estimated_size_sqm}m² · {s.rating ?? '4.5'}★</span>
                  {'concept' in s && (s as { concept?: string }).concept && (
                    <span className="store-concept">{(s as { concept: string }).concept}</span>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="market-assessment">
              No MELLER store in this city yet — expansion opportunity. See{' '}
              <a href="https://mellerbrand.com/pages/our-stores" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--meller-orange)' }}>
                our stores
              </a>.
            </p>
          )}
          {stores.nearby_competitors.length > 0 && (
            <>
              <h4 style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Nearby on Google Maps
              </h4>
              <ul className="store-list">
                {stores.nearby_competitors.slice(0, 4).map((s) => (
                  <li key={s.place_id}>
                    <strong>{s.name}</strong>
                    <span>{s.rating ?? 'N/A'}★ ({s.user_ratings_total} reviews)</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}
    </div>
  );
}
