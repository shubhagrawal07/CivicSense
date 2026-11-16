import L from "leaflet";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import { Link } from "react-router-dom";
import type { MapFeature, Severity } from "../../api/types";
import { ISSUE_STATUS_LABEL } from "../report/statusLabels";

const MUMBAI_CENTER: [number, number] = [19.076, 72.8777];

function buildIcon(modifier: string): L.DivIcon {
  return L.divIcon({
    className: `map-marker map-marker--${modifier}`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -9],
  });
}

const SEVERITY_ICONS: Record<Severity, L.DivIcon> = {
  CRITICAL: buildIcon("critical"),
  HIGH: buildIcon("high"),
  MEDIUM: buildIcon("medium"),
  LOW: buildIcon("low"),
};

const UNCLASSIFIED_ICON = buildIcon("unclassified");

function markerIcon(severity: Severity | null): L.DivIcon {
  return severity ? SEVERITY_ICONS[severity] : UNCLASSIFIED_ICON;
}

export function featurePosition(feature: MapFeature): [number, number] {
  const [lng, lat] = feature.geometry.coordinates;
  return [lat, lng];
}

export function IssuesMap({
  features,
  children,
}: {
  features: MapFeature[];
  children?: React.ReactNode;
}) {
  return (
    <MapContainer center={MUMBAI_CENTER} zoom={11} className="map-container">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <MarkerClusterGroup chunkedLoading>
        {features.map((feature) => (
          <Marker
            key={feature.properties.id}
            position={featurePosition(feature)}
            icon={markerIcon(feature.properties.severity)}
          >
            <Popup>
              <dl>
                <dt>Category</dt>
                <dd>{feature.properties.category}</dd>
                <dt>Severity</dt>
                <dd>{feature.properties.severity ?? "—"}</dd>
                <dt>Status</dt>
                <dd>{ISSUE_STATUS_LABEL[feature.properties.status]}</dd>
                <dt>Reports</dt>
                <dd>{feature.properties.report_count}</dd>
              </dl>
              <Link to={`/issues/${feature.properties.id}`}>View issue</Link>
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>
      {children}
    </MapContainer>
  );
}
