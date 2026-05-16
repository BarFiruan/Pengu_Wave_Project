import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import LoginModal from "./components/LoginModal";
import WelcomeBanner from "./components/WelcomeBanner";
import EventsPage from "./pages/EventsPage";
import UsersPage from "./pages/UsersPage";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./auth/ProtectedRoute";

function App() {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <>
      <Navbar onLoginClick={() => setShowLogin(true)} />
      <div className="container">
        <WelcomeBanner />
        <Routes>
          <Route path="/" element={<Navigate to="/events" replace />} />
          <Route
            path="/events"
            element={
              <ProtectedRoute onLoginRequired={() => setShowLogin(true)}>
                <EventsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute onLoginRequired={() => setShowLogin(true)}>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </>
  );
}

export default App;
