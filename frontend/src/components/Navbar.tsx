import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

interface NavbarProps {
  onLoginClick: () => void;
}

export default function Navbar({ onLoginClick }: NavbarProps) {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/events" style={{ textDecoration: "none", color: "inherit" }}>
          PenguWave 🐧
        </Link>
      </div>
      <div className="navbar-links">
        <Link
          to="/events"
          className={location.pathname.startsWith("/events") ? "active" : ""}
        >
          Events
        </Link>
        {user?.role === "admin" && (
          <Link
            to="/users"
            className={location.pathname === "/users" ? "active" : ""}
          >
            Users
          </Link>
        )}
        {user ? (
          <>
            <span style={{ fontSize: 13, color: "#444" }}>
              {user.email} ({user.role})
            </span>
            <button
              type="button"
              className="navbar-login-btn"
              onClick={() => logout()}
            >
              Logout
            </button>
          </>
        ) : (
          <button type="button" onClick={onLoginClick} className="navbar-login-btn">
            Login
          </button>
        )}
      </div>
    </nav>
  );
}
