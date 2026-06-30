import type { CityLocation } from '../api';

interface Props {
  shortlist: CityLocation[];
  onRemove: (id: string) => void;
  onClear: () => void;
  onSelect: (city: CityLocation) => void;
  onCompare: () => void;
}

export default function ExpansionShortlist({
  shortlist, onRemove, onClear, onSelect, onCompare,
}: Props) {
  if (shortlist.length === 0) return null;

  return (
    <section className="sidebar-section expansion-shortlist">
      <h2>
        Expansion Shortlist
        <span className="prop-count">{shortlist.length}</span>
      </h2>
      <ul className="shortlist">
        {shortlist.map((c) => (
          <li key={c.id}>
            <button type="button" className="shortlist-city" onClick={() => onSelect(c)}>
              <strong>{c.city}</strong>
              <span>{c.country}</span>
              {c.viability_score != null && (
                <span className="shortlist-score">Score {c.viability_score}</span>
              )}
            </button>
            <button type="button" className="shortlist-remove" onClick={() => onRemove(c.id)} aria-label="Remove">×</button>
          </li>
        ))}
      </ul>
      <div className="shortlist-actions">
        {shortlist.length >= 2 && (
          <button type="button" className="compare-run-btn" onClick={onCompare}>
            Compare shortlist
          </button>
        )}
        <button type="button" className="dismiss-btn" onClick={onClear}>Clear</button>
      </div>
    </section>
  );
}
