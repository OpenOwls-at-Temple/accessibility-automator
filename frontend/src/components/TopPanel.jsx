import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.jsx";

// Top panel of the home page: the signed-in user's name and email (Feature 2).
export default function TopPanel() {
  const { user, logout } = useAuth();
  return (
    <div className="card row spread">
      <div>
        <div style={{ color: "var(--text-head)", fontWeight: 600, fontSize: 18 }}>
          {user.name || user.email}
        </div>
        <div className="muted">{user.email}</div>
      </div>
      <div className="row" style={{ gap: 10 }}>
        {user.is_admin && (
          <Link className="btn-link" to="/admin">
            Manage users
          </Link>
        )}
        <button className="secondary" onClick={logout}>
          Sign out
        </button>
      </div>
    </div>
  );
}
