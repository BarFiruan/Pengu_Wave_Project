/**
 * Sign-in dialog. Calls AuthContext.login (cookie set by the backend).
 *
 * Shows server error messages inline and only closes on success—the
 * original starter closed even when login failed.
 */

import { useState } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface LoginModalProps {
  onClose: () => void;
}

export default function LoginModal({ onClose }: LoginModalProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      onClose();
    } catch (err) {
      // Surface the generic server message (e.g. "Invalid email or password").
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Unable to sign in. Is the backend running?");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button">
          ✕
        </button>
        <h2>Sign In</h2>
        <p style={{ color: "#666", marginBottom: 20, fontSize: 14 }}>
          Enter your credentials to access PenguWave
        </p>
        {error && (
          <p style={{ color: "#c00", marginBottom: 12, fontSize: 14 }} role="alert">
            {error}
          </p>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
            />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            style={{ width: "100%" }}
            disabled={submitting}
          >
            {submitting ? "Signing in…" : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
