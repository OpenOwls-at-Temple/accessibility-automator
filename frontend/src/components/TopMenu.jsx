import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.jsx";

// The app's top navigation menu, shared across authenticated pages.
// Manage users appears only for admins.
export default function TopMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const signOut = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="app-nav">
      <NavLink to="/" end className="brand">
        🦉 Accessibility Automator
      </NavLink>
      <div className="nav-links">
        <NavLink to="/" end className="nav-link">
          Workspace
        </NavLink>
        <NavLink to="/settings" className="nav-link">
          Settings
        </NavLink>
        {user?.is_admin && (
          <NavLink to="/admin" className="nav-link">
            Manage users
          </NavLink>
        )}
        <button className="nav-link nav-signout" onClick={signOut}>
          Sign out
        </button>
      </div>
    </nav>
  );
}
