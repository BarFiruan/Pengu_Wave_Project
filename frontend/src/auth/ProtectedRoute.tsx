/**
 * Blocks page content until the user is authenticated.
 *
 * Shows a sign-in prompt and calls onLoginRequired so the parent can open
 * the login modal. This is UX only—the API still returns 401 without a
 * valid cookie.
 */

import type { ReactNode } from "react";
import { useAuth } from "./AuthContext";

interface ProtectedRouteProps {
  children: ReactNode;
  onLoginRequired: () => void;
}

export default function ProtectedRoute({ children, onLoginRequired }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <p style={{ color: "#666" }}>Loading session…</p>;
  }

  if (!user) {
    onLoginRequired();
    return (
      <div className="page-container">
        <p style={{ color: "#666" }}>Please sign in to view this page.</p>
      </div>
    );
  }

  return <>{children}</>;
}
