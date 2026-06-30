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

function getMarkerColor(viability?: number): string {
  if (!viability) return '#71717a';
  if (viability >= 75) return '#4ade80';
  if (viability >= 55) return '#fbbf24';
  if (viability >= 35) return '#fb923c';
  return '#f87171';
}

function getMarkerRadius(population: number): number {
  return Math.max(6, Math.min(18, Math.sqrt(population / 50000)));
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
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <FitBounds cities={cities} />
      {cities.map((city) => {
        const pred = predictions[city.id];
        const isSelected = selectedCity?.id === city.id;
        const isHovered = hoveredId === city.id;
        const color = getMarkerColor(pred?.viability_score);

        return (
          <CircleMarker
            key={city.id}
            center={[city.latitude, city.longitude]}
            radius={getMarkerRadius(city.population) * (isSelected || isHovered ? 1.3 : 1)}
            pathOptions={{
              color: isSelected ? '#c8a96e' : color,
              fillColor: color,
              fillOpacity: isSelected ? 0.9 : 0.7,
              weight: isSelected ? 3 : 1.5,
            }}
            eventHandlers={{
              click: () => onSelectCity(city),
              mouseover: () => setHoveredId(city.id),
              mouseout: () => setHoveredId(null),
            }}
          >
            <Popup>
              <div style={{ color: '#1a1a1e', minWidth: 180 }}>
                <strong>{city.city}, {city.country}</strong>
                {pred && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontSize: '1.1em', fontWeight: 700, color: '#a68b4b' }}>
                      {formatCurrency(pred.predicted_annual_revenue_eur)}
                    </div>
                    <div style={{ fontSize: '0.85em', color: '#666' }}>
                      {pred.viability_label}
                    </div>
                  </div>
                )}
                {city.has_existing_store && (
                  <div style={{ marginTop: 6, fontSize: '0.8em', color: '#a68b4b' }}>
                    Existing Meller store
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
