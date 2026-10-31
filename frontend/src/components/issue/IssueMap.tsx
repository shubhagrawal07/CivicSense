import { MapContainer, Marker, TileLayer } from "react-leaflet";

interface IssueMapProps {
  lat: number;
  lng: number;
}

export function IssueMap({ lat, lng }: IssueMapProps) {
  return (
    <MapContainer
      center={[lat, lng]}
      zoom={15}
      scrollWheelZoom={false}
      style={{ height: 240, width: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <Marker position={[lat, lng]} />
    </MapContainer>
  );
}
