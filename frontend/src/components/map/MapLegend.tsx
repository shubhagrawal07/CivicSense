import { SEVERITY_LEGEND } from "./severity";

export function MapLegend() {
  return (
    <ul className="map-legend">
      {SEVERITY_LEGEND.map((entry) => (
        <li key={entry.label}>
          <span className="map-legend__swatch" style={{ background: entry.color }} />
          {entry.label}
        </li>
      ))}
    </ul>
  );
}
