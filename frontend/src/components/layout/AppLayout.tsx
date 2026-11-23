import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div>
      <Header onToggleMenu={() => setSidebarOpen(!sidebarOpen)} />
      <div className="app-body">
        <Sidebar open={sidebarOpen} />
        <div className="app-content">
          <main className="app-main">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
