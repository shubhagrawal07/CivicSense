import { useState } from "react";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";

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

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const [geoError, setGeoError] = useState<string | null>(null);

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setGeoError("Location is not supported on this device.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setGeoError(null);
        onChange({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
      },
      () => {
        setGeoError("Could not access your location. Click the map instead.");
      },
    );
  }

  return (
    <div>
      <label>Location</label>
      <button type="button" onClick={useCurrentLocation}>
        Use my current location
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
        {value && <Marker position={value} />}
      </MapContainer>
    </div>
  );
}
