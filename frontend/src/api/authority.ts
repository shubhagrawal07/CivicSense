import { client } from "./client";
import { env } from "../config/env";
import type { AuthorityInfo, Department, JurisdictionAt } from "./types";

async function realGetDepartments(): Promise<Department[]> {
  const { data } = await client.get<Department[]>("/departments");
  return data;
}

async function realGetJurisdictionsAt(lat: number, lng: number): Promise<JurisdictionAt[]> {
  const { data } = await client.get<JurisdictionAt[]>("/jurisdictions/at", {
    params: { lat, lng },
  });
  return data;
}

async function realGetAuthorityInfo(
  departmentId: number,
  lat: number,
  lng: number,
): Promise<AuthorityInfo> {
  const { data } = await client.get<AuthorityInfo>("/authority-info", {
    params: { department_id: departmentId, lat, lng },
  });
  return data;
}

const MOCK_DEPARTMENTS: Department[] = [
  { id: 1, name: "Roads / Public Works" },
  { id: 3, name: "Water Supply" },
  { id: 6, name: "General Grievance" },
];

const BMC = { id: 1, name: "Brihanmumbai Municipal Corporation", jurisdiction: "Mumbai" };
const IITB = { id: 2, name: "IIT Bombay Campus Administration", jurisdiction: "IIT Bombay campus" };

// south of 19.0 is outside every area, east of 72.9 is the campus, the rest is a ward
function mockAreaAt(lat: number, lng: number): JurisdictionAt[] {
  if (lat < 19.0) return [];
  if (lng >= 72.9) {
    return [{ id: 2, name: "IIT Bombay campus", type: "campus", priority: 20, authority: IITB }];
  }
  return [{ id: 1, name: "Ward K East", type: "ward", priority: 10, authority: BMC }];
}

async function mockGetDepartments(): Promise<Department[]> {
  return MOCK_DEPARTMENTS;
}

async function mockGetJurisdictionsAt(lat: number, lng: number): Promise<JurisdictionAt[]> {
  return mockAreaAt(lat, lng);
}

async function mockGetAuthorityInfo(
  departmentId: number,
  lat: number,
  lng: number,
): Promise<AuthorityInfo> {
  const department = MOCK_DEPARTMENTS.find((d) => d.id === departmentId) ?? MOCK_DEPARTMENTS[0];
  const authority = mockAreaAt(lat, lng)[0]?.authority ?? BMC;
  return {
    department,
    authority,
    contacts: [
      {
        type: "HELPLINE",
        value: "1916",
        source_url: "https://portal.mcgm.gov.in",
        last_verified_at: "2026-11-06",
        verified: true,
      },
      {
        type: "EMAIL",
        value: "helpdesk@example.org",
        source_url: null,
        last_verified_at: null,
        verified: false,
      },
    ],
    is_fallback: false,
    needs_review: false,
    other_matches: [],
  };
}

export const getDepartments: () => Promise<Department[]> = env.useMockApi
  ? mockGetDepartments
  : realGetDepartments;

export const getJurisdictionsAt: (lat: number, lng: number) => Promise<JurisdictionAt[]> =
  env.useMockApi ? mockGetJurisdictionsAt : realGetJurisdictionsAt;

export const getAuthorityInfo: (
  departmentId: number,
  lat: number,
  lng: number,
) => Promise<AuthorityInfo> = env.useMockApi ? mockGetAuthorityInfo : realGetAuthorityInfo;
