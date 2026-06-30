import { useState } from 'react';
import type { CityComparisonResult, CityLocation } from '../api';
import { compareCities, formatCurrency } from '../api';

interface Props {
  cities: CityLocation[];
  storeSize: number;
  selectedCity: CityLocation | null;
  shortlist: CityLocation[];
}

export default function ComparePanel({ cities, storeSize, selectedCity, shortlist }: Props) {
  const [selected, setSelected] = useState<string[]>(
    shortlist.length >= 2
      ? shortlist.slice(0, 3).map((c) => c.id)
      : selectedCity ? [selectedCity.id] : [],
  );
  const [result, setResult] = useState<CityComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggle = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 5 ? [...prev, id] : prev,
    );
  };

  const runCompare = async () => {
    if (selected.length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const data = await compareCities(selected, storeSize);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  const pool = shortlist.length > 0 ? shortlist : cities.slice(0, 30);

  return (
    <div className="compare-panel">
      <section className="sidebar-section">
        <h2>Compare Cities for Expansion</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Select 2–5 cities to compare revenue, viability, and market fundamentals side-by-side.
        </p>

        <div className="compare-picker">
          {pool.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`compare-chip ${selected.includes(c.id) ? 'selected' : ''}`}
              onClick={() => toggle(c.id)}
            >
              {c.city} {selected.includes(c.id) && '✓'}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="compare-run-btn"
          disabled={selected.length < 2 || loading}
          onClick={runCompare}
        >
          {loading ? 'Comparing…' : `Compare ${selected.length} cities`}
        </button>
        {error && <p style={{ color: 'var(--danger)', fontSize: '0.85rem', marginTop: '0.5rem' }}>{error}</p>}
      </section>

      {result && (
        <>
          <section className="sidebar-section">
            <h2>Winner</h2>
            {result.winner && (
              <div className="winner-card">
                <strong>{result.winner.city}, {result.winner.country}</strong>
                <span className="winner-rev">{formatCurrency(result.winner.predicted_revenue_eur)}/yr</span>
                <span>Viability {result.winner.viability_score}/100 — {result.winner.viability_label}</span>
              </div>
            )}
            <p className="recommendation" style={{ marginTop: '0.75rem' }}>{result.summary}</p>
          </section>

          <section className="sidebar-section">
            <h2>Side-by-Side</h2>
            <div className="compare-table-wrap">
              <table className="compare-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    {result.cities.map((c) => (
                      <th key={c.city_id}>{c.city}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Revenue/yr</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>{formatCurrency(c.predicted_revenue_eur)}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>Viability</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id} className={c.viability_score >= 55 ? 'high' : ''}>{c.viability_score}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>€/m²</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>{formatCurrency(c.revenue_per_sqm)}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>Foot traffic</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>{c.foot_traffic_index}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>Tourist index</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>{c.tourist_index}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>GDP/capita</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>€{c.gdp_per_capita.toLocaleString()}</td>
                    ))}
                  </tr>
                  <tr>
                    <td>MELLER store</td>
                    {result.cities.map((c) => (
                      <td key={c.city_id}>{c.has_existing_store ? 'Yes' : 'No'}</td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
