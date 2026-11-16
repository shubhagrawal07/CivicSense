import { client } from "./client";
import type { HotspotCell } from "./types";

export async function getHotspots(category?: string): Promise<HotspotCell[]> {
  const { data } = await client.get<HotspotCell[]>("/hotspots", {
    params: category ? { category } : {},
  });
  return data;
}
