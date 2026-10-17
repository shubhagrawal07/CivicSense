import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";
import { env } from "../config/env";

// Minimal auth stub for SL-15. SL-24 (login pages) will replace the
// internals of this provider (real login call, token refresh, etc.)
// without changing how ProtectedRoute or consumers use this context.

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readInitialToken(): string | null {
  const stored = localStorage.getItem("authToken");
  if (stored) return stored;
  return env.useMockApi && env.devAuthToken ? env.devAuthToken : null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(readInitialToken);

  const login = useCallback((newToken: string) => {
    localStorage.setItem("authToken", newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("authToken");
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
