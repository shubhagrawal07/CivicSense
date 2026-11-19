import { useEffect, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { GEO_OPTIONS, geoErrorMessage } from "./geoErrors";

export interface LatLng {
  lat: number;
  lng: number;
}

interface LocationPickerProps {
  value: LatLng | null;
  onChange: (value: LatLng) => void;
}

const DEFAULT_CENTER: LatLng = { lat: 19.076, lng: 72.8777 }; // Mumbai, as a reasonable default

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
