import type { HealthStatus } from '../api';

interface Props {
  health: HealthStatus | null;
  dataWarning?: string | null;
}

export default function DataStatusBanner({ health, dataWarning }: Props) {
  if (!health && !dataWarning) return null;

  const googleLive = health?.google_maps_live;
  const googleConfigured = health?.google_maps_enabled;
  const googleError = health?.google_api_error;

  let message: string | null = dataWarning ?? null;
  let variant: 'info' | 'warning' | 'ok' = 'info';

  if (!message && googleConfigured && !googleLive) {
    message = googleError
      ? `Google Maps live data unavailable: ${googleError}`
      : 'Google Maps API key is set but live data is not flowing. Enable Places API (New) in Google Cloud Console.';
    variant = 'warning';
  } else if (!message && !googleConfigured) {
    message = 'Using estimated data — set GOOGLE_MAPS_API_KEY for live Google Maps store and review data.';
    variant = 'info';
  } else if (!message && googleLive) {
    message = 'Live Google Maps data active';
    variant = 'ok';
  }

  if (!message) return null;

  return (
    <div className={`data-status-banner data-status-${variant}`}>
      {message}
      {variant === 'warning' && (
        <a
          href="https://console.cloud.google.com/apis/library/places.googleapis.com"
          target="_blank"
          rel="noopener noreferrer"
        >
          Enable Places API
        </a>
      )}
    </div>
  );
}
