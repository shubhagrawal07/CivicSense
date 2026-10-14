import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { ReportNewPage } from "./pages/ReportNewPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* TODO(SL-24): add /login route */}
        <Route
          path="/report/new"
          element={
            <ProtectedRoute>
              <ReportNewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports/:id"
          element={
            <ProtectedRoute>
              <ReportDetailPage />
            </ProtectedRoute>
          }
        />
        {/* TODO(SL-27): add /my-reports route */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
