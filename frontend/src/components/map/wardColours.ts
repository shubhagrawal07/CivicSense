export interface WardRange {
  min: number;
  max: number;
  colour: string;
}

const COLOURS = ["#fff3e0", "#ffcc80", "#ff9800", "#e65100", "#8d2f00"];

export function buildWardRanges(highestCount: number): WardRange[] {
  const size = Math.max(1, Math.ceil(highestCount / COLOURS.length));
  return COLOURS.map((colour, index) => ({
    min: index === 0 ? 0 : index * size + 1,
    max: (index + 1) * size,
    colour,
  }));
}

export function wardColour(count: number, ranges: WardRange[]): string {
  const range = ranges.find((r) => count >= r.min && count <= r.max);
  return range ? range.colour : ranges[ranges.length - 1].colour;
}
