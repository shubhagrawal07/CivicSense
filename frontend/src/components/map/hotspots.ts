export interface HotspotStep {
  label: string;
  color: string;
  radius: number;
  minScore: number;
}

export const HOTSPOT_STEPS: HotspotStep[] = [
  { label: "10 and above", color: "#b71c1c", radius: 550, minScore: 10 },
  { label: "5 to 10", color: "#e65100", radius: 450, minScore: 5 },
  { label: "2 to 5", color: "#f9a825", radius: 350, minScore: 2 },
  { label: "Under 2", color: "#fdd835", radius: 250, minScore: 0 },
];

export function hotspotStep(score: number): HotspotStep {
  return (
    HOTSPOT_STEPS.find((step) => score >= step.minScore) ?? HOTSPOT_STEPS[HOTSPOT_STEPS.length - 1]
  );
}

export const HOTSPOT_LEGEND = HOTSPOT_STEPS.map((step) => ({
  label: step.label,
  color: step.color,
}));
