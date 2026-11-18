import type { WardRange } from "./wardColours";

export function WardLegend({ ranges }: { ranges: WardRange[] }) {
  return (
    <ul className="map-legend">
      {ranges.map((range) => (
        <li key={range.min}>
          <span className="ward-swatch" style={{ background: range.colour }} />
          {range.min === range.max ? range.min : `${range.min}–${range.max}`} issues
        </li>
      ))}
    </ul>
  );
}
