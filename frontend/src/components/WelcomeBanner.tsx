import { useState } from "react";

export default function WelcomeBanner() {
  const [dismissed, setDismissed] = useState(() => {
    return sessionStorage.getItem("welcome-dismissed") === "true";
  });

  if (dismissed) return null;

  const handleDismiss = () => {
    sessionStorage.setItem("welcome-dismissed", "true");
    setDismissed(true);
  };

  return (
    <div className="welcome-banner">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: "0 0 8px", fontSize: 16 }}>
            Welcome to PenguWave
          </h2>
          <p style={{ margin: 0, color: "#555", fontSize: 13 }}>
            Sign in to view security events. Admins can manage users from the Users page.
            See <code>README.md</code> and <code>THREAT_MODEL.md</code> for setup and security details.
          </p>
        </div>
        <button
          type="button"
          onClick={handleDismiss}
          style={{
            background: "none",
            border: "none",
            fontSize: 18,
            cursor: "pointer",
            color: "#999",
            padding: "0 0 0 12px",
            lineHeight: 1,
          }}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
