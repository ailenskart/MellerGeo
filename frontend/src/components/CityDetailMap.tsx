import { useEffect } from 'react';
import { CircleMarker, MapContainer, Polygon, Popup, TileLayer, useMap } from 'react-leaflet';
import type { CatchmentArea, CityLocation, CommercialProperty, StreetLocation } from '../api';
import { formatCurrency } from '../api';

const MELLER_ORANGE = '#FF6723';
const PROPERTY_BLUE = '#3b82f6';

interface Props {
  city: CityLocation;
  catchments: CatchmentArea[];
  streets: StreetLocation[];
  properties: CommercialProperty[];
  selectedCatchment: CatchmentArea | null;
  selectedStreet: StreetLocation | null;
  selectedProperty: CommercialProperty | null;
  onSelectCatchment: (c: CatchmentArea) => void;
  onSelectStreet: (s: StreetLocation) => void;
  onSelectProperty: (p: CommercialProperty) => void;
}

function getViabilityColor(score: number): string {
  if (score >= 75) return '#22c55e';
  if (score >= 55) return MELLER_ORANGE;
  if (score >= 35) return '#f59e0b';
  return '#ef4444';
}

function FlyToCity({ city, selectedStreet, selectedCatchment, selectedProperty }: {
  city: CityLocation;
  selectedStreet: StreetLocation | null;
  selectedCatchment: CatchmentArea | null;
  selectedProperty: CommercialProperty | null;
}) {
  const map = useMap();
  useEffect(() => {
    if (selectedProperty) {
      map.flyTo([selectedProperty.latitude, selectedProperty.longitude], 17, { duration: 0.8 });
    } else if (selectedStreet) {
      map.flyTo([selectedStreet.latitude, selectedStreet.longitude], 17, { duration: 0.8 });
    } else if (selectedCatchment) {
      map.flyTo([selectedCatchment.center.latitude, selectedCatchment.center.longitude], 15, { duration: 0.8 });
    } else {
      map.flyTo([city.latitude, city.longitude], 13, { duration: 0.8 });
    }
  }, [city, selectedStreet, selectedCatchment, selectedProperty, map]);
  return null;
}

export default function CityDetailMap({
  city,
  catchments,
  streets,
  properties,
  selectedCatchment,
  selectedStreet,
  selectedProperty,
  onSelectCatchment,
  onSelectStreet,
  onSelectProperty,
}: Props) {
  const visibleStreets = selectedCatchment
    ? streets.filter((s) => s.catchment_id === selectedCatchment.id)
    : streets;

  const visibleProperties = selectedCatchment
    ? properties.filter((p) => !p.catchment_id || p.catchment_id === selectedCatchment.id)
    : properties;

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
      <FlyToCity
        city={city}
        selectedStreet={selectedStreet}
        selectedCatchment={selectedCatchment}
        selectedProperty={selectedProperty}
      />

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
              </div>
            </Popup>
          </CircleMarker>
        );
      })}

      {visibleProperties.map((p) => {
        const isSelected = selectedProperty?.id === p.id;
        return (
          <CircleMarker
            key={p.id}
            center={[p.latitude, p.longitude]}
            radius={isSelected ? 9 : 7}
            pathOptions={{
              color: isSelected ? '#111' : PROPERTY_BLUE,
              fillColor: PROPERTY_BLUE,
              fillOpacity: 0.85,
              weight: isSelected ? 3 : 2,
            }}
            eventHandlers={{ click: () => onSelectProperty(p) }}
          >
            <Popup>
              <div style={{ fontFamily: 'Helvetica Neue, sans-serif', minWidth: 240 }}>
                <div style={{ fontSize: '0.7em', color: PROPERTY_BLUE, fontWeight: 700, textTransform: 'uppercase' }}>
                  {p.broker} · {p.availability_label}
                </div>
                <strong style={{ display: 'block', marginTop: 4 }}>{p.title}</strong>
                <div style={{ fontSize: '0.8em', color: '#666', marginTop: 4 }}>{p.address}</div>
                <div style={{ fontSize: '0.95em', marginTop: 8 }}>
                  {p.size_sqm} m² · {formatCurrency(p.rent_eur_monthly)}/mo
                </div>
                <div style={{ fontSize: '0.85em', color: MELLER_ORANGE, fontWeight: 700, marginTop: 4 }}>
                  MELLER fit: {p.meller_fit_score}/100
                </div>
                {p.street_name && (
                  <div style={{ fontSize: '0.8em', marginTop: 4 }}>Near: {p.street_name}</div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
