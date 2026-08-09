import { Navigate, Outlet } from "react-router-dom";

export function RequireAuth() {
  const token = localStorage.getItem("calvio_token");
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function saveToken(token) {
  localStorage.setItem("calvio_token", token);
}

export function clearToken() {
  localStorage.removeItem("calvio_token");
}
