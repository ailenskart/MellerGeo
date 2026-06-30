import { useState } from 'react';
import type { HealthStatus } from '../api';

interface Props {
  health: HealthStatus | null;
  dataWarning?: string | null;
}

export default function DataStatusBanner({ health, dataWarning }: Props) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;
  if (!health && !dataWarning) return null;

  const mapsLive = health?.maps_live;
  const liveSource = health?.maps_live_source;
  const googleLive = health?.google_maps_live;
  const osmLive = health?.osm_live;
  const googleConfigured = health?.google_maps_enabled;
  const googleError = health?.google_api_error;
  const enableUrl = health?.google_enable_url;

  let message: string | null = dataWarning ?? null;
  let variant: 'info' | 'warning' | 'ok' = 'info';
  let dismissible = false;

  if (!message && mapsLive && osmLive) {
    message = 'Live store data active via OpenStreetMap';
    variant = 'ok';
  } else if (!message && mapsLive && googleLive) {
    message = 'Live Google Maps data active';
    variant = 'ok';
  } else if (!message && googleConfigured && !mapsLive && googleError) {
    message = 'Using estimated data — Google Maps not enabled. App works without it.';
    variant = 'info';
    dismissible = true;
  } else if (!message && !googleConfigured) {
    message = null;
  }

  if (!message) return null;

  return (
    <div className={`data-status-banner data-status-${variant}`}>
      <div className="data-status-content">
        <span>{message}</span>
        {liveSource && variant === 'ok' && (
          <span className="data-status-steps">Source: {liveSource}</span>
        )}
      </div>
      <div className="data-status-actions">
        {variant === 'info' && enableUrl && (
          <a href={enableUrl} target="_blank" rel="noopener noreferrer">
            Fix Google Maps (optional)
          </a>
        )}
        {dismissible && (
          <button type="button" className="dismiss-btn" onClick={() => setDismissed(true)}>
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}
