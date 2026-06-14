import { useAuth } from "../hooks/useAuth.jsx";

// Top panel of the home page: the signed-in user's name and email (Feature 2).
export default function TopPanel() {
  const { user, logout } = useAuth();
  return (
    <div className="card row spread">
      <div>
        <div style={{ color: "var(--text-head)", fontWeight: 600, fontSize: 18 }}>
          {user.name}
        </div>
        <div className="muted">{user.email}</div>
      </div>
      <button className="secondary" onClick={logout}>
        Sign out
      </button>
    </div>
  );
}
