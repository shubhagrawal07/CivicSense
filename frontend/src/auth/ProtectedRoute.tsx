import type { ReactNode } from "react";
import { useAuth } from "./AuthContext";

// Placeholder until SL-24 adds a real /login route: rather than redirecting
// to a route that doesn't exist yet, this renders an inline message.
// SL-24 can later change this to <Navigate to="/login" /> without touching
// any call site that wraps a route in <ProtectedRoute>.
export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <div role="alert">
        <p>Please log in to continue.</p>
      </div>
    );
  }

  return <>{children}</>;
}
