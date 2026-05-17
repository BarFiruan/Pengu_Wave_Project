/**
 * Hides UI from users without the required role.
 *
 * This is convenience for the user, NOT a security boundary. The server
 * returns 403 on every /api/users request from non-admins regardless of
 * what the frontend renders.
 */

import type { ReactNode } from "react";
import { useAuth } from "./AuthContext";

interface RequireRoleProps {
  role: string;
  children: ReactNode;
}

export default function RequireRole({ role, children }: RequireRoleProps) {
  const { user } = useAuth();

  if (!user || user.role !== role) {
    return (
      <div className="page-container">
        <h1>Access denied</h1>
        <p style={{ color: "#666" }}>You do not have permission to view this page.</p>
      </div>
    );
  }

  return <>{children}</>;
}
