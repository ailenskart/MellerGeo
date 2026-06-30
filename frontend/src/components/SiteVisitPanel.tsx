import type { SiteVisitContext } from '../api';

interface Props {
  siteVisit: SiteVisitContext | null;
  loading: boolean;
}

export default function SiteVisitPanel({ siteVisit, loading }: Props) {
  if (loading) {
    return <div className="loading">Loading street-level site visit data…</div>;
  }

  if (!siteVisit) {
    return (
      <div className="empty-state" style={{ padding: '2rem 1rem' }}>
        <p>Select a city and drill to a street or catchment to explore Street View, satellite imagery, and site visit checklists.</p>
      </div>
    );
  }

  const sv = siteVisit.street_view;
  const sat = siteVisit.satellite;

  return (
    <div className="site-visit-panel">
      <section className="sidebar-section">
        <h2>Site Visit — {siteVisit.label}</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          {siteVisit.city}, {siteVisit.country}
        </p>
        <div className="city-meta" style={{ marginTop: '0.5rem' }}>
          <span className="badge">Foot traffic {siteVisit.foot_traffic_index}</span>
          <span className="badge">Tourist {siteVisit.tourist_index}</span>
          <span className="badge">Viability {siteVisit.viability_score}</span>
        </div>
        <p className="recommendation" style={{ marginTop: '1rem' }}>{siteVisit.site_assessment}</p>
      </section>

      <section className="sidebar-section">
        <h2>Street View</h2>
        {sv.embed_url ? (
          <div className="embed-frame">
            <iframe
              title="Google Street View"
              src={sv.embed_url}
              width="100%"
              height="260"
              style={{ border: 0, borderRadius: 4 }}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
            />
          </div>
        ) : sv.static_image_url ? (
          <img src={sv.static_image_url} alt="Street view" className="street-view-img" />
        ) : (
          <div className="street-view-fallback">
            <p>Street View embed requires Google Maps Embed API enabled.</p>
            <a href={sv.open_url} target="_blank" rel="noopener noreferrer" className="visit-link-btn">
              Open Street View in Google Maps →
            </a>
          </div>
        )}
        <div className="map-link-row">
          <a href={siteVisit.map_links.mapillary} target="_blank" rel="noopener noreferrer">Mapillary photos</a>
          <a href={siteVisit.map_links.openstreetmap} target="_blank" rel="noopener noreferrer">OpenStreetMap</a>
          <a href={siteVisit.map_links.google_earth} target="_blank" rel="noopener noreferrer">Google Earth</a>
        </div>
      </section>

      {sat.embed_url && (
        <section className="sidebar-section">
          <h2>Satellite</h2>
          <div className="embed-frame">
            <iframe
              title="Satellite view"
              src={sat.embed_url}
              width="100%"
              height="220"
              style={{ border: 0, borderRadius: 4 }}
              allowFullScreen
              loading="lazy"
            />
          </div>
        </section>
      )}

      {siteVisit.wikimedia_photos.length > 0 && (
        <section className="sidebar-section">
          <h2>Nearby Street Photos</h2>
          <div className="photo-grid">
            {siteVisit.wikimedia_photos.map((p) => (
              <a key={p.page_url} href={p.page_url} target="_blank" rel="noopener noreferrer" className="photo-card">
                <img src={p.thumbnail_url} alt={p.title} />
                <span>{p.title.slice(0, 40)}</span>
              </a>
            ))}
          </div>
        </section>
      )}

      <section className="sidebar-section">
        <h2>Expansion Checklist</h2>
        <ul className="checklist">
          {siteVisit.expansion_checklist.map((item, i) => (
            <li key={i} className={`checklist-${item.category}`}>
              <span className="checklist-cat">{item.category}</span>
              {item.item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
