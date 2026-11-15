import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

export type Point = [number, number];

const MUMBAI_CENTER: Point = [19.076, 72.8777];

const PICKED_ICON = L.divIcon({
  className: "map-marker map-marker--picked",
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

function ClickCatcher({ onPick }: { onPick: (point: Point) => void }) {
  useMapEvents({
    click(event) {
      onPick([event.latlng.lat, event.latlng.lng]);
    },
  });
  return null;
}

function FlyTo({ target }: { target: Point | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target, 15);
  }, [map, target]);
  return null;
}

interface Props {
  point: Point | null;
  flyTarget: Point | null;
  onPick: (point: Point) => void;
}

export function AuthorityPicker({ point, flyTarget, onPick }: Props) {
  return (
    <MapContainer center={MUMBAI_CENTER} zoom={11} className="map-container">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <ClickCatcher onPick={onPick} />
      <FlyTo target={flyTarget} />
      {point && <Marker position={point} icon={PICKED_ICON} />}
    </MapContainer>
  );
}
