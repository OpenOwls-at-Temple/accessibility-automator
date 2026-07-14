import { useAuth } from "../hooks/useAuth.jsx";

// Top panel of the workspace: the signed-in user's name and email (Feature 2).
// Navigation and sign-out live in the top menu (TopMenu).
export default function TopPanel() {
  const { user } = useAuth();
  return (
    <div className="card row spread">
      <div>
        <div style={{ color: "var(--text-head)", fontWeight: 600, fontSize: 18 }}>
          {user.name || user.email}
        </div>
        <div className="muted">{user.email}</div>
      </div>
    </div>
  );
}
