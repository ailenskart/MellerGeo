import type { CatchmentArea, CityLocation, CommercialProperty, CommercialPropertySearch, StreetLocation } from '../api';
import { formatCurrency } from '../api';
import CommercialPropertiesPanel from './CommercialPropertiesPanel';

interface Props {
  city: CityLocation;
  catchments: CatchmentArea[];
  streets: StreetLocation[];
  selectedCatchment: CatchmentArea | null;
  selectedStreet: StreetLocation | null;
  onSelectCatchment: (c: CatchmentArea | null) => void;
  onSelectStreet: (s: StreetLocation | null) => void;
  onOpenSocial?: () => void;
  properties?: CommercialPropertySearch | null;
  propertiesLoading?: boolean;
  selectedPropertyId?: string | null;
  onSelectProperty?: (p: CommercialProperty) => void;
  loading: boolean;
}

function viabilityClass(score: number): string {
  if (score >= 55) return 'high';
  if (score >= 35) return 'medium';
  return 'low';
}

export default function LocationPanel({
  city,
  catchments,
  streets,
  selectedCatchment,
  selectedStreet,
  onSelectCatchment,
  onSelectStreet,
  onOpenSocial,
  properties,
  propertiesLoading,
  selectedPropertyId,
  onSelectProperty,
  loading,
}: Props) {
  if (loading) {
    return <div className="loading">Loading catchments & streets...</div>;
  }

  const filteredStreets = selectedCatchment
    ? streets.filter((s) => s.catchment_id === selectedCatchment.id)
    : streets;

  return (
    <div className="location-panel">
      <div className="breadcrumb">
        <button type="button" onClick={() => { onSelectStreet(null); onSelectCatchment(null); }}>
          {city.city}
        </button>
        {selectedCatchment && (
          <>
            <span>/</span>
            <button type="button" onClick={() => onSelectStreet(null)}>
              {selectedCatchment.name}
            </button>
          </>
        )}
        {selectedStreet && (
          <>
            <span>/</span>
            <span className="breadcrumb-current">{selectedStreet.name}</span>
          </>
        )}
      </div>

      {onOpenSocial && (
        <p className="tab-hint">
          Google reviews, Instagram buzz, and shopping signals are in the{' '}
          <button type="button" onClick={onOpenSocial}>Social tab</button>.
        </p>
      )}

      {selectedStreet ? (
        <section className="sidebar-section">
          <h2>Street Analysis</h2>
          <h3 style={{ fontSize: '1.1rem', textTransform: 'none', letterSpacing: 0 }}>{selectedStreet.name}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {selectedStreet.catchment_name} · {selectedStreet.type_label}
          </p>
          <div className="city-meta">
            {selectedStreet.has_meller_store && <span className="badge existing">MELLER Store</span>}
            <span className="badge">Foot traffic {selectedStreet.foot_traffic_index}</span>
            <span className="badge">Rent index {selectedStreet.retail_rent_index}</span>
            {selectedStreet.street_width_m && <span className="badge">{selectedStreet.street_width_m}m wide</span>}
          </div>

          <div className="revenue-card" style={{ marginTop: '1rem' }}>
            <div className="revenue-main">{formatCurrency(selectedStreet.predicted_annual_revenue_eur)}</div>
            {selectedStreet.confidence_interval_low != null && (
              <div className="revenue-range">
                Range: {formatCurrency(selectedStreet.confidence_interval_low)} – {formatCurrency(selectedStreet.confidence_interval_high!)}
              </div>
            )}
            <div className="revenue-per-sqm">{formatCurrency(selectedStreet.revenue_per_sqm)} / m²</div>
            <div className="viability">
              <div className={`viability-score ${viabilityClass(selectedStreet.viability_score)}`}>
                {selectedStreet.viability_score}
              </div>
              <div>
                <div className="viability-label">{selectedStreet.viability_label}</div>
              </div>
            </div>
          </div>

          <p className="recommendation" style={{ marginTop: '1rem' }}>{selectedStreet.recommendation}</p>

          <CommercialPropertiesPanel
            properties={properties ?? null}
            loading={!!propertiesLoading}
            selectedPropertyId={selectedPropertyId}
            onSelectProperty={onSelectProperty}
          />
        </section>
      ) : selectedCatchment ? (
        <>
          <section className="sidebar-section">
            <h2>Catchment Area</h2>
            <h3 style={{ fontSize: '1.1rem', textTransform: 'none' }}>{selectedCatchment.name}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{selectedCatchment.type_label}</p>
            <div className="revenue-card" style={{ marginTop: '1rem' }}>
              <div className="revenue-main">{formatCurrency(selectedCatchment.predicted_annual_revenue_eur)}</div>
              <div className="revenue-per-sqm">{formatCurrency(selectedCatchment.revenue_per_sqm)} / m²</div>
              <div className="viability">
                <div className={`viability-score ${viabilityClass(selectedCatchment.viability_score)}`}>
                  {selectedCatchment.viability_score}
                </div>
                <div className="viability-label">{selectedCatchment.viability_label}</div>
              </div>
            </div>
            <div className="catchment-metrics">
              <div><span>Tourist</span><strong>{selectedCatchment.tourist_index}</strong></div>
              <div><span>Luxury retail</span><strong>{selectedCatchment.luxury_retail_score}</strong></div>
              <div><span>Foot traffic</span><strong>{selectedCatchment.foot_traffic_index}</strong></div>
              <div><span>Rent index</span><strong>{selectedCatchment.retail_rent_index}</strong></div>
            </div>
            <p className="recommendation" style={{ marginTop: '1rem' }}>{selectedCatchment.recommendation}</p>
          </section>

          <section className="sidebar-section">
            <h2>Streets in {selectedCatchment.name}</h2>
            <ul className="location-list">
              {filteredStreets.map((s) => (
                <li
                  key={s.id}
                  className={s.has_meller_store ? 'has-meller' : ''}
                  onClick={() => onSelectStreet(s)}
                >
                  <div className="location-list-name">{s.name}</div>
                  <div className="location-list-meta">
                    <span>{s.type_label}</span>
                    <span className="location-list-rev">{formatCurrency(s.predicted_annual_revenue_eur)}</span>
                    <span className={`viability-pill ${viabilityClass(s.viability_score)}`}>{s.viability_score}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <CommercialPropertiesPanel
            properties={properties ?? null}
            loading={!!propertiesLoading}
            selectedPropertyId={selectedPropertyId}
            onSelectProperty={onSelectProperty}
          />
        </>
      ) : (
        <>
          <section className="sidebar-section">
            <h2>Where to open in {city.city}</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              Select a catchment area on the map, then drill down to street level to find the best MELLER Factory location.
            </p>
            {catchments[0] && (
              <div className="top-pick">
                <span className="top-pick-label">Top catchment</span>
                <strong>{catchments[0].name}</strong>
                <span>{formatCurrency(catchments[0].predicted_annual_revenue_eur)} · Score {catchments[0].viability_score}</span>
              </div>
            )}
          </section>

          <section className="sidebar-section">
            <h2>Catchment Areas ({catchments.length})</h2>
            <ul className="location-list">
              {catchments.map((c) => (
                <li
                  key={c.id}
                  className={c.has_meller_store ? 'has-meller' : ''}
                  onClick={() => onSelectCatchment(c)}
                >
                  <div className="location-list-name">
                    {c.name}
                    {c.has_meller_store && <span className="badge existing" style={{ marginLeft: 8 }}>MELLER</span>}
                  </div>
                  <div className="location-list-meta">
                    <span>{c.type_label}</span>
                    <span>{c.street_count} streets</span>
                    <span className="location-list-rev">{formatCurrency(c.predicted_annual_revenue_eur)}</span>
                    <span className={`viability-pill ${viabilityClass(c.viability_score)}`}>{c.viability_score}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="sidebar-section">
            <h2>Top Streets</h2>
            <ul className="location-list">
              {streets.slice(0, 5).map((s) => (
                <li key={s.id} onClick={() => {
                  const c = catchments.find((x) => x.id === s.catchment_id);
                  if (c) onSelectCatchment(c);
                  onSelectStreet(s);
                }}>
                  <div className="location-list-name">{s.name}</div>
                  <div className="location-list-meta">
                    <span>{s.catchment_name}</span>
                    <span className="location-list-rev">{formatCurrency(s.predicted_annual_revenue_eur)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <CommercialPropertiesPanel
            properties={properties ?? null}
            loading={!!propertiesLoading}
            selectedPropertyId={selectedPropertyId}
            onSelectProperty={onSelectProperty}
          />
        </>
      )}
    </div>
  );
}
