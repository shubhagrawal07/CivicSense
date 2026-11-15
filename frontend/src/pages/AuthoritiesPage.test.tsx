import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthorityInfo, Department, JurisdictionAt } from "../api/types";
import { AuthoritiesPage } from "./AuthoritiesPage";

const api = vi.hoisted(() => ({
  departments: vi.fn(),
  areas: vi.fn(),
  info: vi.fn(),
}));

vi.mock("../api/authority", () => ({
  getDepartments: () => api.departments(),
  getJurisdictionsAt: (lat: number, lng: number) => api.areas(lat, lng),
  getAuthorityInfo: (id: number, lat: number, lng: number) => api.info(id, lat, lng),
}));

// leaflet needs real layout, so the map is replaced by buttons that pick a point
vi.mock("../components/map/AuthorityPicker", () => ({
  AuthorityPicker: ({ onPick }: { onPick: (point: [number, number]) => void }) => (
    <div>
      <button onClick={() => onPick([19.05, 72.85])}>pick ward</button>
      <button onClick={() => onPick([19.13, 72.91])}>pick campus</button>
      <button onClick={() => onPick([18.5, 72.8])}>pick nowhere</button>
    </div>
  ),
}));

const departments: Department[] = [
  { id: 1, name: "Roads / Public Works" },
  { id: 3, name: "Water Supply" },
];

const bmc = { id: 1, name: "BMC Roads Department", jurisdiction: "Mumbai" };
const iitb = { id: 2, name: "IIT Bombay Civil Maintenance", jurisdiction: "IIT Bombay campus" };

function areaFor(name: string, type: string, authority = bmc): JurisdictionAt[] {
  return [{ id: 1, name, type, priority: 10, authority }];
}

function infoFor(department: Department, overrides: Partial<AuthorityInfo> = {}): AuthorityInfo {
  return {
    department,
    authority: bmc,
    contacts: [
      {
        type: "HELPLINE",
        value: "1916",
        source_url: "https://example.org/source",
        last_verified_at: "2026-11-06",
        verified: true,
      },
      {
        type: "EMAIL",
        value: "help@example.org",
        source_url: null,
        last_verified_at: null,
        verified: false,
      },
    ],
    is_fallback: false,
    needs_review: false,
    other_matches: [],
    ...overrides,
  };
}

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthoritiesPage />
    </MemoryRouter>,
  );
}

async function locateButton() {
  const button = await screen.findByRole("button", { name: "Use my location" });
  await waitFor(() => expect(button).toBeEnabled());
  return button;
}

async function pickPoint(label: string) {
  await locateButton();
  fireEvent.click(screen.getByText(label));
}

describe("AuthoritiesPage", () => {
  beforeEach(() => {
    api.departments.mockReset().mockResolvedValue(departments);
    api.areas.mockReset().mockResolvedValue(areaFor("Ward K East", "ward"));
    api.info
      .mockReset()
      .mockImplementation((id: number) =>
        Promise.resolve(infoFor(departments.find((d) => d.id === id) as Department)),
      );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("asks for a point before anything is looked up", async () => {
    renderPage();
    expect(await screen.findByText("No point chosen yet.")).toBeInTheDocument();
    expect(api.areas).not.toHaveBeenCalled();
  });

  it("shows the area, the authority and each department's contacts", async () => {
    renderPage();
    await pickPoint("pick ward");

    expect(await screen.findByText("Ward K East")).toBeInTheDocument();
    expect(api.areas).toHaveBeenCalledWith(19.05, 72.85);
    expect(api.info).toHaveBeenCalledWith(1, 19.05, 72.85);
    expect(api.info).toHaveBeenCalledWith(3, 19.05, 72.85);
    expect(screen.getByText("Roads / Public Works")).toBeInTheDocument();
    expect(screen.getByText("Water Supply")).toBeInTheDocument();
    expect(screen.getAllByText("1916")).toHaveLength(2);
  });

  it("shows the source and verification date, and marks only unverified contacts", async () => {
    api.departments.mockResolvedValue([departments[0]]);
    renderPage();
    await pickPoint("pick ward");

    const source = await screen.findByRole("link", { name: "Source" });
    expect(source).toHaveAttribute("href", "https://example.org/source");
    expect(screen.getByText("2026-11-06")).toBeInTheDocument();
    expect(screen.getByText("No source")).toBeInTheDocument();
    expect(screen.getByText("Not recorded")).toBeInTheDocument();
    expect(screen.getAllByText("Unverified")).toHaveLength(1);
    expect(screen.getByRole("link", { name: "help@example.org" })).toHaveAttribute(
      "href",
      "mailto:help@example.org",
    );
  });

  it("shows a different area when another point is clicked", async () => {
    api.areas.mockImplementation((lat: number) =>
      Promise.resolve(
        lat > 19.1 ? areaFor("IIT Bombay campus", "campus", iitb) : areaFor("Ward K East", "ward"),
      ),
    );
    renderPage();

    await pickPoint("pick ward");
    expect(await screen.findByText("Ward K East")).toBeInTheDocument();

    fireEvent.click(screen.getByText("pick campus"));
    expect(await screen.findByText("IIT Bombay campus")).toBeInTheDocument();
    expect(screen.queryByText("Ward K East")).not.toBeInTheDocument();
    expect(screen.getByText(/handled by/)).toHaveTextContent("IIT Bombay Civil Maintenance");
  });

  it("explains the default authority when no area matches, and still lists contacts", async () => {
    api.areas.mockResolvedValue([]);
    renderPage();
    await pickPoint("pick nowhere");

    expect(await screen.findByText(/No ward or campus covers this point/)).toBeInTheDocument();
    expect(screen.getAllByText("1916").length).toBeGreaterThan(0);
  });

  it("says when a department is showing the general grievance contacts", async () => {
    api.departments.mockResolvedValue([departments[1]]);
    api.info.mockResolvedValue(infoFor(departments[1], { is_fallback: true }));
    renderPage();
    await pickPoint("pick ward");

    expect(await screen.findByText(/no contacts of its own/)).toBeInTheDocument();
  });

  it("names the other candidates when the point is near a boundary", async () => {
    api.departments.mockResolvedValue([departments[0]]);
    api.info.mockResolvedValue(
      infoFor(departments[0], { needs_review: true, other_matches: [iitb] }),
    );
    renderPage();
    await pickPoint("pick ward");

    expect(await screen.findByText(/close to an area boundary/)).toHaveTextContent(
      "IIT Bombay Civil Maintenance",
    );
  });

  it("shows an error when a lookup fails", async () => {
    api.areas.mockRejectedValue(new Error("boom"));
    renderPage();
    await pickPoint("pick ward");

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });

  it("looks up the browser's position when asked", async () => {
    vi.stubGlobal("navigator", {
      geolocation: {
        getCurrentPosition: (ok: (p: GeolocationPosition) => void) =>
          ok({ coords: { latitude: 19.1334, longitude: 72.9133 } } as GeolocationPosition),
      },
    });
    renderPage();

    fireEvent.click(await locateButton());

    await waitFor(() => expect(api.areas).toHaveBeenCalledWith(19.1334, 72.9133));
  });

  it("tells the user when the location cannot be read", async () => {
    vi.stubGlobal("navigator", {
      geolocation: {
        getCurrentPosition: (_ok: unknown, fail: () => void) => fail(),
      },
    });
    renderPage();

    fireEvent.click(await locateButton());

    expect(await screen.findByText(/Could not get your location/)).toBeInTheDocument();
    expect(api.areas).not.toHaveBeenCalled();
  });
});
