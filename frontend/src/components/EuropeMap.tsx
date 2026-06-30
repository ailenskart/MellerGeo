import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import type { CityLocation, RevenuePrediction } from '../api';
import { formatCurrency } from '../api';

interface Props {
  cities: CityLocation[];
  selectedCity: CityLocation | null;
  onSelectCity: (city: CityLocation) => void;
  predictions: Record<string, RevenuePrediction>;
}

const MELLER_ORANGE = '#FF6723';

function getMarkerColor(viability?: number, hasStore?: boolean): string {
  if (hasStore) return MELLER_ORANGE;
  if (!viability) return '#999999';
  if (viability >= 75) return '#22c55e';
  if (viability >= 55) return '#FF6723';
  if (viability >= 35) return '#f59e0b';
  return '#ef4444';
}

function getMarkerRadius(population: number, hasStore?: boolean): number {
  const base = Math.max(5, Math.min(16, Math.sqrt(population / 50000)));
  return hasStore ? base * 1.4 : base;
}

function FitBounds({ cities }: { cities: CityLocation[] }) {
  const map = useMap();
  useEffect(() => {
    if (cities.length > 0) {
      const bounds = cities.map((c) => [c.latitude, c.longitude] as [number, number]);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [cities, map]);
  return null;
}

export default function EuropeMap({ cities, selectedCity, onSelectCity, predictions }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <MapContainer center={[48.5, 10]} zoom={5} zoomControl={true}>
      <TileLayer
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      <FitBounds cities={cities} />
      {cities.map((city) => {
        const pred = predictions[city.id];
        const isSelected = selectedCity?.id === city.id;
        const isHovered = hoveredId === city.id;
        const color = getMarkerColor(pred?.viability_score, city.has_existing_store);

        return (
          <CircleMarker
            key={city.id}
            center={[city.latitude, city.longitude]}
            radius={getMarkerRadius(city.population, city.has_existing_store) * (isSelected || isHovered ? 1.3 : 1)}
            pathOptions={{
              color: isSelected ? '#111111' : color,
              fillColor: color,
              fillOpacity: isSelected ? 0.95 : 0.75,
              weight: isSelected ? 3 : city.has_existing_store ? 2.5 : 1.5,
            }}
            eventHandlers={{
              click: () => onSelectCity(city),
              mouseover: () => setHoveredId(city.id),
              mouseout: () => setHoveredId(null),
            }}
          >
            <Popup>
              <div style={{ color: '#111', minWidth: 180, fontFamily: 'Helvetica Neue, sans-serif' }}>
                <strong style={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {city.city}, {city.country}
                </strong>
                {pred && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: '1.1em', fontWeight: 700, color: MELLER_ORANGE }}>
                      {formatCurrency(pred.predicted_annual_revenue_eur)}
                    </div>
                    <div style={{ fontSize: '0.85em', color: '#666' }}>
                      {pred.viability_label}
                    </div>
                  </div>
                )}
                {city.has_existing_store && (
                  <div style={{ marginTop: 6, fontSize: '0.75em', color: MELLER_ORANGE, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    MELLER Store
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
