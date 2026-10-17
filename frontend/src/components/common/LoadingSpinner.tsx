export function LoadingSpinner({ label = "Loading…" }: { label?: string }) {
  return <p role="status">{label}</p>;
}
