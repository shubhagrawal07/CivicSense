import { useEffect, useRef, useState } from "react";
import { getAuthorityInfo, getDepartments, getJurisdictionsAt } from "../api/authority";
import { parseApiError } from "../api/errors";
import type { AuthorityInfo, Department, JurisdictionAt } from "../api/types";
import { DepartmentContacts } from "../components/authority/DepartmentContacts";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { AuthorityPicker, type Point } from "../components/map/AuthorityPicker";

type Lookup =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; areas: JurisdictionAt[]; infos: AuthorityInfo[] };

function AreaSummary({ areas }: { areas: JurisdictionAt[] }) {
  if (areas.length === 0) {
    return (
      <p>
        No ward or campus covers this point, so the default authority of each department applies.
      </p>
    );
  }
  const [main, ...others] = areas;
  return (
    <div>
      <p>
        Area: <strong>{main.name}</strong> ({main.type})
        {main.authority && (
          <>
            , handled by <strong>{main.authority.name}</strong>
          </>
        )}
      </p>
      {others.length > 0 && <p>Also inside: {others.map((a) => a.name).join(", ")}</p>}
    </div>
  );
}

export function AuthoritiesPage() {
  const [departments, setDepartments] = useState<Department[] | null>(null);
  const [departmentError, setDepartmentError] = useState<string | null>(null);
  const [point, setPoint] = useState<Point | null>(null);
  const [flyTarget, setFlyTarget] = useState<Point | null>(null);
  const [lookup, setLookup] = useState<Lookup>({ kind: "idle" });
  const [locationError, setLocationError] = useState<string | null>(null);
  const latestRequest = useRef(0);

  useEffect(() => {
    let active = true;
    getDepartments()
      .then((list) => {
        if (active) setDepartments(list);
      })
      .catch((err) => {
        if (active) setDepartmentError(parseApiError(err).message);
      });
    return () => {
      active = false;
    };
  }, []);

  function pick(next: Point) {
    if (!departments) return;
    setPoint(next);
    setLocationError(null);
    setLookup({ kind: "loading" });

    const request = ++latestRequest.current;
    const [lat, lng] = next;
    Promise.all([
      getJurisdictionsAt(lat, lng),
      Promise.all(departments.map((d) => getAuthorityInfo(d.id, lat, lng))),
    ])
      .then(([areas, infos]) => {
        if (request === latestRequest.current) setLookup({ kind: "ready", areas, infos });
      })
      .catch((err) => {
        if (request === latestRequest.current) {
          setLookup({ kind: "error", message: parseApiError(err).message });
        }
      });
  }

  function locateMe() {
    if (!navigator.geolocation) {
      setLocationError("Your browser does not support location.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const here: Point = [position.coords.latitude, position.coords.longitude];
        setFlyTarget(here);
        pick(here);
      },
      () => setLocationError("Could not get your location. Click on the map instead."),
    );
  }

  return (
    <div>
      <h2>Who is responsible here?</h2>
      <p>Click a point on the map to see the authority and contacts for each department.</p>
      <button type="button" onClick={locateMe} disabled={!departments}>
        Use my location
      </button>
      {locationError && <p role="alert">{locationError}</p>}
      {departmentError && <ErrorBanner message={departmentError} />}

      <AuthorityPicker point={point} flyTarget={flyTarget} onPick={pick} />

      {lookup.kind === "idle" && !departmentError && <p>No point chosen yet.</p>}
      {lookup.kind === "loading" && <LoadingSpinner label="Looking up authorities…" />}
      {lookup.kind === "error" && <ErrorBanner message={lookup.message} />}
      {lookup.kind === "ready" && (
        <div>
          <AreaSummary areas={lookup.areas} />
          {lookup.infos.map((info) => (
            <DepartmentContacts key={info.department.id} info={info} />
          ))}
        </div>
      )}
    </div>
  );
}
