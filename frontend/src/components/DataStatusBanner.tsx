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
  const enableUrl = health?.google_enable_url;
  const fixInstructions = health?.google_fix_instructions;

  let message: string | null = dataWarning ?? null;
  let variant: 'info' | 'warning' | 'ok' = 'info';

  if (!message && googleConfigured && !googleLive) {
    message = googleError
      ?? 'Places API (New) is not enabled. Enable it in Google Cloud Console to get live store and review data.';
    variant = 'warning';
  } else if (!message && !googleConfigured) {
    message = 'Using estimated data — set GOOGLE_MAPS_API_KEY for live Google Maps store and review data.';
    variant = 'info';
  } else if (!message && googleLive) {
    message = 'Live Google Maps data active (Places API New)';
    variant = 'ok';
  }

  if (!message) return null;

  return (
    <div className={`data-status-banner data-status-${variant}`}>
      <div className="data-status-content">
        <span>{message}</span>
        {variant === 'warning' && fixInstructions && (
          <span className="data-status-steps">{fixInstructions}</span>
        )}
      </div>
      {variant === 'warning' && enableUrl && (
        <a href={enableUrl} target="_blank" rel="noopener noreferrer">
          Enable Places API (New)
        </a>
      )}
    </div>
  );
}
