import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout, isLoading } = useAuth();

  return (
    <header className="app-header">
      <strong>CivicSense</strong>
      {!isLoading && (
        <nav>
          {user ? (
            <>
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
