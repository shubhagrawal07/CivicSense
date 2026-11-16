interface MapLegendProps {
  entries: { label: string; color: string }[];
}

export function MapLegend({ entries }: MapLegendProps) {
  return (
    <ul className="map-legend">
      {entries.map((entry) => (
        <li key={entry.label}>
          <span className="map-legend__swatch" style={{ background: entry.color }} />
          {entry.label}
        </li>
      ))}
    </ul>
  );
}
