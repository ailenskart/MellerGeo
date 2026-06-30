import type { CommercialProperty, CommercialPropertySearch } from '../api';
import { formatCurrency } from '../api';

interface Props {
  properties: CommercialPropertySearch | null;
  loading: boolean;
  selectedPropertyId?: string | null;
  onSelectProperty?: (p: CommercialProperty) => void;
}

function fitClass(score: number): string {
  if (score >= 75) return 'high';
  if (score >= 55) return 'medium';
  return 'low';
}

function availabilityClass(status: string): string {
  if (status === 'available') return 'avail';
  if (status === 'under_offer') return 'offer';
  return 'let';
}

export default function CommercialPropertiesPanel({
  properties,
  loading,
  selectedPropertyId,
  onSelectProperty,
}: Props) {
  if (loading) {
    return <div className="loading">Searching JLL, CBRE, Savills & broker listings…</div>;
  }

  if (!properties || properties.listings.length === 0) {
    return (
      <section className="sidebar-section">
        <h2>Commercial Properties</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          No retail units found. Listings from JLL, CBRE, Cushman & Wakefield, Savills, Knight Frank, and Colliers appear here when available.
        </p>
      </section>
    );
  }

  return (
    <section className="sidebar-section commercial-properties">
      <h2>
        Commercial Properties
        <span className="prop-count">{properties.available_count} available</span>
      </h2>
      <p className="prop-summary">{properties.summary}</p>
      <div className="broker-tags">
        {properties.brokers.map((b) => (
          <span key={b} className="broker-tag">{b}</span>
        ))}
      </div>

      <ul className="property-list">
        {properties.listings.map((p) => (
          <li
            key={p.id}
            className={`property-item ${selectedPropertyId === p.id ? 'selected' : ''} ${availabilityClass(p.availability)}`}
            onClick={() => onSelectProperty?.(p)}
          >
            <div className="property-header">
              <strong>{p.title}</strong>
              <span className={`avail-badge ${availabilityClass(p.availability)}`}>{p.availability_label}</span>
            </div>
            <div className="property-broker">
              <span className="broker-name">{p.broker}</span>
              {p.street_name && <span className="prop-street">· {p.street_name}</span>}
            </div>
            <p className="property-address">{p.address}</p>
            <div className="property-metrics">
              <span>{p.size_sqm} m²</span>
              <span>{formatCurrency(p.rent_eur_monthly)}/mo</span>
              <span>€{p.rent_eur_sqm_year}/m²/yr</span>
            </div>
            <div className="property-footer">
              <span className={`fit-score ${fitClass(p.meller_fit_score)}`}>
                MELLER fit {p.meller_fit_score}
              </span>
              <span className="prop-type">{p.property_type_label}</span>
            </div>
            {p.broker_portal && (
              <a
                href={p.broker_portal}
                target="_blank"
                rel="noopener noreferrer"
                className="prop-link"
                onClick={(e) => e.stopPropagation()}
              >
                View on {p.broker} →
              </a>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
