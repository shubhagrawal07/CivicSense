import { Circle, Popup } from "react-leaflet";
import type { HotspotCell } from "../../api/types";
import { hotspotStep } from "./hotspots";

export function HotspotLayer({ cells }: { cells: HotspotCell[] }) {
  return (
    <>
      {cells.map((cell) => {
        const step = hotspotStep(cell.score);
        return (
          <Circle
            key={`${cell.lat},${cell.lng}`}
            center={[cell.lat, cell.lng]}
            radius={step.radius}
            pathOptions={{ color: step.color, fillColor: step.color, fillOpacity: 0.4 }}
          >
            <Popup>
              <dl>
                <dt>Issues</dt>
                <dd>{cell.count}</dd>
                <dt>Score</dt>
                <dd>{cell.score.toFixed(1)}</dd>
              </dl>
            </Popup>
          </Circle>
        );
      })}
    </>
  );
}
