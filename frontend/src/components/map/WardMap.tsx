import type { Layer } from "leaflet";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import type { WardCount, WardFeatureCollection } from "../../api/types";
import { wardColour } from "./wardColours";
import type { WardRange } from "./wardColours";

const MUMBAI_CENTER: [number, number] = [19.076, 72.8777];

interface WardMapProps {
  wards: WardFeatureCollection;
  counts: WardCount[];
  ranges: WardRange[];
}

export function WardMap({ wards, counts, ranges }: WardMapProps) {
  const countById: Record<number, WardCount> = {};
  for (const row of counts) {
    countById[row.ward_id] = row;
  }

  function styleWard(feature?: { properties: { id: number } | null }) {
    const id = feature?.properties?.id ?? 0;
    const issueCount = countById[id]?.issue_count ?? 0;
    return {
      fillColor: wardColour(issueCount, ranges),
      fillOpacity: 0.8,
      color: "#555",
      weight: 1,
    };
  }

  function addTooltip(feature: { properties: { id: number; name: string } }, layer: Layer) {
    const row = countById[feature.properties.id];
    const text = document.createElement("div");
    text.textContent =
      `${feature.properties.name}: ${row?.issue_count ?? 0} issues, ` +
      `${row?.open_count ?? 0} open`;
    layer.bindTooltip(text, { sticky: true });
  }

  return (
    <MapContainer center={MUMBAI_CENTER} zoom={11} className="map-container">
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />
      <GeoJSON data={wards} style={styleWard} onEachFeature={addTooltip} />
    </MapContainer>
  );
}
