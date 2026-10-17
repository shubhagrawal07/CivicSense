export function ErrorBanner({ message }: { message: string }) {
  return (
    <div role="alert" style={{ color: "#b00020" }}>
      {message}
    </div>
  );
}
