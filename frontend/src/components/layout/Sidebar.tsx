import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Sidebar({ open }: { open: boolean }) {
  const { user } = useAuth();

  return (
    <aside className={open ? "sidebar sidebar--open" : "sidebar"}>
      <nav>
        <NavLink to="/" end>Home</NavLink>
        <NavLink to="/dashboard">Dashboard</NavLink>
        <NavLink to="/trends">Trends</NavLink>
        <NavLink to="/map">Map</NavLink>
        <NavLink to="/ward-map">Ward map</NavLink>
        <NavLink to="/authorities">Authorities</NavLink>
        <NavLink to="/data">Data</NavLink>
        <NavLink to="/report/new">Raise a report</NavLink>
        <NavLink to="/my-reports">My reports</NavLink>
        {user?.role === "ADMIN" && <NavLink to="/admin/data-quality">Data quality</NavLink>}
      </nav>
    </aside>
  );
}
