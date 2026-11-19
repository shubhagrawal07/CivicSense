import type { MapFeature } from "../../api/types";

export function featurePosition(feature: MapFeature): [number, number] {
  const [lng, lat] = feature.geometry.coordinates;
  return [lat, lng];
}
