import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

const THEMES = [
  { value: "light", label: "Light mode" },
  { value: "dark", label: "Dark mode" },
  { value: "solar", label: "Solar mode" },
];

export function Header({ onToggleMenu }: { onToggleMenu: () => void }) {
  const { user, logout, isLoading } = useAuth();
  const [profileOpen, setProfileOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("theme") ?? "light");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);

  function closeMenus() {
    setProfileOpen(false);
    setSettingsOpen(false);
  }

  function handleLogout() {
    closeMenus();
    logout();
  }

  return (
    <header className="app-header">
      <div className="header-left">
        <button
          type="button"
          className="icon-button"
          aria-label="Open menu"
          onClick={onToggleMenu}
        >
          ☰
        </button>
      </div>

      <Link to="/" className="app-title">
        <strong>CivicSense</strong>
      </Link>

      <div className="header-right">
        <Link className="nav-button" to="/dashboard">Dashboard</Link>
        <Link className="nav-button" to="/my-reports">My reports</Link>
        <Link className="nav-button" to="/report/new">Raise a report</Link>
        {!isLoading && (
          <div className="header-profile">
            <button
              type="button"
              className="icon-button"
              aria-label="Profile"
              onClick={() => {
                setProfileOpen(!profileOpen);
              }}
            >
              👤
            </button>
            {profileOpen && (
              <div className="dropdown dropdown--right">
                {user ? (
                  <>
                    <span>{user.name}</span>
                    <button type="button" className="nav-button" onClick={handleLogout}>
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <Link to="/login" onClick={closeMenus}>Log in</Link>
                    <Link to="/register" onClick={closeMenus}>Register</Link>
                  </>
                )}
                <button
                  type="button"
                  className="theme-option"
                  onClick={() => setSettingsOpen(!settingsOpen)}
                >
                  Settings
                </button>
                {settingsOpen && (
                  <div className="theme-options">
                    {THEMES.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={
                          theme === option.value
                            ? "theme-option theme-option--selected"
                            : "theme-option"
                        }
                        onClick={() => setTheme(option.value)}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
