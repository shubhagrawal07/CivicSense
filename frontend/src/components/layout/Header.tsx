import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout, isLoading } = useAuth();

  return (
    <header className="app-header">
      <strong>CivicSense</strong>
      {!isLoading && (
        <nav>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/data">Data</Link>
          {user ? (
            <>
              {user.role === "ADMIN" && <Link to="/admin/data-quality">Data quality</Link>}
              <span>{user.name}</span>
              <button type="button" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Log in</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
