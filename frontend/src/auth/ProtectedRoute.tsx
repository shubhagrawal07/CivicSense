import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import type { UserRole } from "../api/types";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({ children, role }: { children: ReactNode; role?: UserRole }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  if (role && user?.role !== role) return <Navigate to="/" replace />;
  return <>{children}</>;
}
