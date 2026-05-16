/**
 * Admin-only user management UI.
 *
 * Wrapped in RequireRole for navigation clarity; DELETE/POST still require
 * admin on the server. Passwords are never shown in the table (API omits them).
 */

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import * as usersApi from "../api/users";
import RequireRole from "../auth/RequireRole";
import type { User } from "../types";

export default function UsersPage() {
  return (
    <RequireRole role="admin">
      <UsersPageContent />
    </RequireRole>
  );
}

function UsersPageContent() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState("analyst");
  const [formError, setFormError] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await usersApi.getUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail || !newPassword) return;
    setFormError(null);
    try {
      await usersApi.createUser({
        email: newEmail,
        password: newPassword,
        role: newRole,
      });
      setNewEmail("");
      setNewPassword("");
      setNewRole("analyst");
      setShowForm(false);
      await loadUsers();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create user");
    }
  };

  const handleDelete = async (id: string, email: string) => {
    // Confirm before irreversible delete; server also blocks self-delete and last admin.
    if (!window.confirm(`Delete user ${email}?`)) return;
    try {
      await usersApi.deleteUser(id);
      await loadUsers();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Failed to delete user");
    }
  };

  if (loading) {
    return <p style={{ color: "#666" }}>Loading users…</p>;
  }

  if (error) {
    return <p style={{ color: "#c00" }}>{error}</p>;
  }

  return (
    <div className="page-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1>User Management</h1>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add User"}
        </button>
      </div>

      {showForm && (
        <div style={{ border: "1px solid #ddd", padding: 16, marginBottom: 20, background: "#fafafa" }}>
          <h3 style={{ marginBottom: 12 }}>New User</h3>
          {formError && <p style={{ color: "#c00", fontSize: 14 }}>{formError}</p>}
          <form onSubmit={handleAddUser}>
            <div style={{ marginBottom: 8 }}>
              <label>Email</label>
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="user@penguwave.io"
                required
              />
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="password"
                required
                minLength={8}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label>Role</label>
              <select value={newRole} onChange={(e) => setNewRole(e.target.value)}>
                <option value="admin">Admin</option>
                <option value="analyst">Analyst</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
            <button type="submit" className="btn-primary">
              Create User
            </button>
          </form>
        </div>
      )}

      <table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <span style={{ color: user.status === "active" ? "green" : "#999" }}>
                  {user.status}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  onClick={() => handleDelete(user.id, user.email)}
                  style={{ color: "red", background: "none", border: "none", cursor: "pointer", padding: 0 }}
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {users.length === 0 && <p style={{ color: "#999" }}>No users yet.</p>}
    </div>
  );
}
