const PERMISSION_DENIED = 1;
const POSITION_UNAVAILABLE = 2;
const TIMEOUT = 3;

export const GEO_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 0,
};

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
