import { useEffect, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

export interface LatLng {
  lat: number;
  lng: number;
}

interface LocationPickerProps {
  value: LatLng | null;
  onChange: (value: LatLng) => void;
}

const DEFAULT_CENTER: LatLng = { lat: 19.076, lng: 72.8777 }; // Mumbai, as a reasonable default

const GEO_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 0,
};

const PERMISSION_DENIED = 1;
const POSITION_UNAVAILABLE = 2;
const TIMEOUT = 3;

export function geoErrorMessage(code: number): string {
  if (code === PERMISSION_DENIED) {
    return "Location permission is blocked. Allow it in your browser settings, or click the map instead.";
  }
  if (code === POSITION_UNAVAILABLE) {
    return "Your location is not available right now. Click the map instead.";
  }
  if (code === TIMEOUT) {
    return "Finding your location took too long. Try again, or click the map instead.";
  }
  return "Could not access your location. Click the map instead.";
}

function ClickHandler({ onChange }: { onChange: (value: LatLng) => void }) {
  useMapEvents({
    click(event) {
      onChange({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });
  return null;
}

function Recenter({ value }: { value: LatLng | null }) {
  const map = useMap();
  useEffect(() => {
    if (value) {
      map.setView([value.lat, value.lng], map.getZoom());
    }
  }, [map, value]);
  return null;
}

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const [geoError, setGeoError] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);

  function findCurrentLocation() {
    if (!navigator.geolocation) {
      setGeoError("Location is not supported on this device. Click the map instead.");
      return;
    }
    setGeoError(null);
    setSearching(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setSearching(false);
        onChange({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      (error) => {
        setSearching(false);
        setGeoError(geoErrorMessage(error.code));
      },
      GEO_OPTIONS,
    );
  }

  return (
    <div>
      <label>Location</label>
      <button type="button" onClick={findCurrentLocation} disabled={searching}>
        {searching ? "Finding your location…" : "Use my current location"}
      </button>
      {geoError && <p role="alert">{geoError}</p>}
      <MapContainer
        center={value ?? DEFAULT_CENTER}
        zoom={13}
        style={{ height: 300, width: "100%", marginTop: 12 }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        <ClickHandler onChange={onChange} />
        <Recenter value={value} />
        {value && <Marker position={value} />}
      </MapContainer>
    </div>
  );
}
