import { useEffect } from 'react';
import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, useMap } from 'react-leaflet';
import type { CatchmentArea, CityLocation, StreetLocation } from '../api';
import { formatCurrency } from '../api';

const MELLER_ORANGE = '#FF6723';

interface Props {
  city: CityLocation;
  catchments: CatchmentArea[];
  streets: StreetLocation[];
  selectedCatchment: CatchmentArea | null;
  selectedStreet: StreetLocation | null;
  onSelectCatchment: (c: CatchmentArea) => void;
  onSelectStreet: (s: StreetLocation) => void;
}

function getViabilityColor(score: number): string {
  if (score >= 75) return '#22c55e';
  if (score >= 55) return MELLER_ORANGE;
  if (score >= 35) return '#f59e0b';
  return '#ef4444';
}

function FlyToCity({ city, selectedStreet, selectedCatchment }: {
  city: CityLocation;
  selectedStreet: StreetLocation | null;
  selectedCatchment: CatchmentArea | null;
}) {
  const map = useMap();
  useEffect(() => {
    if (selectedStreet) {
      map.flyTo([selectedStreet.latitude, selectedStreet.longitude], 17, { duration: 0.8 });
    } else if (selectedCatchment) {
      map.flyTo([selectedCatchment.center.latitude, selectedCatchment.center.longitude], 15, { duration: 0.8 });
    } else {
      map.flyTo([city.latitude, city.longitude], 13, { duration: 0.8 });
    }
  }, [city, selectedStreet, selectedCatchment, map]);
  return null;
}

export default function CityDetailMap({
  city,
  catchments,
  streets,
  selectedCatchment,
  selectedStreet,
  onSelectCatchment,
  onSelectStreet,
}: Props) {
  const visibleStreets = selectedCatchment
    ? streets.filter((s) => s.catchment_id === selectedCatchment.id)
    : streets;

  return (
    <MapContainer
      center={[city.latitude, city.longitude]}
      zoom={13}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
      />
      <FlyToCity city={city} selectedStreet={selectedStreet} selectedCatchment={selectedCatchment} />

      {catchments.map((c) => {
        const isSelected = selectedCatchment?.id === c.id;
        const color = c.has_meller_store ? MELLER_ORANGE : getViabilityColor(c.viability_score);
        const positions = c.polygon.map((p) => [p[0], p[1]] as [number, number]);

        return (
          <Polygon
            key={c.id}
            positions={positions}
            pathOptions={{
              color: isSelected ? '#111' : color,
              fillColor: color,
              fillOpacity: isSelected ? 0.35 : 0.2,
              weight: isSelected ? 3 : 1.5,
            }}
            eventHandlers={{ click: () => onSelectCatchment(c) }}
          >
            <Popup>
              <div style={{ fontFamily: 'Helvetica Neue, sans-serif', minWidth: 200 }}>
                <strong style={{ textTransform: 'uppercase' }}>{c.name}</strong>
                <div style={{ fontSize: '0.8em', color: '#666', marginTop: 4 }}>{c.type_label}</div>
                <div style={{ fontSize: '1.1em', fontWeight: 700, color: MELLER_ORANGE, marginTop: 8 }}>
                  {formatCurrency(c.predicted_annual_revenue_eur)}
                </div>
                <div style={{ fontSize: '0.85em' }}>{c.viability_label} · {c.street_count} streets</div>
              </div>
            </Popup>
          </Polygon>
        );
      })}

      {visibleStreets.map((s) => {
        const isSelected = selectedStreet?.id === s.id;
        const color = s.has_meller_store ? MELLER_ORANGE : getViabilityColor(s.viability_score);

        return (
          <CircleMarker
            key={s.id}
            center={[s.latitude, s.longitude]}
            radius={isSelected ? 10 : s.has_meller_store ? 8 : 6}
            pathOptions={{
              color: isSelected ? '#111' : color,
              fillColor: color,
              fillOpacity: 0.9,
              weight: isSelected ? 3 : 2,
            }}
            eventHandlers={{ click: () => onSelectStreet(s) }}
          >
            <Popup>
              <div style={{ fontFamily: 'Helvetica Neue, sans-serif', minWidth: 220 }}>
                <strong>{s.name}</strong>
                <div style={{ fontSize: '0.8em', color: '#666' }}>{s.type_label}</div>
                <div style={{ fontSize: '1.1em', fontWeight: 700, color: MELLER_ORANGE, marginTop: 8 }}>
                  {formatCurrency(s.predicted_annual_revenue_eur)}
                </div>
                <div style={{ fontSize: '0.85em' }}>Foot traffic: {s.foot_traffic_index}/100</div>
                {s.has_meller_store && (
                  <div style={{ color: MELLER_ORANGE, fontWeight: 700, fontSize: '0.75em', marginTop: 4, textTransform: 'uppercase' }}>
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
