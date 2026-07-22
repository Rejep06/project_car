import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { useAuth } from "./AuthContext";

export function AdminRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading)
    return (
      <div className="page-center">
        <LoadingSpinner label="Проверяем административную сессию" />
      </div>
    );
  if (!user || user.role !== "admin")
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
