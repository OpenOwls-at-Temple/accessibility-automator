import { useCallback, useEffect, useState } from "react";
import TopMenu from "../components/TopMenu.jsx";
import { api } from "../services/api.js";
import { useAuth } from "../hooks/useAuth.jsx";

// Admin-only: the invite mechanism. Admins add Temple users to the allowlist
// (only added accounts can sign in), and activate/deactivate them.
export default function AdminUsers() {
  const { user, loading } = useAuth();
  const [users, setUsers] = useState([]);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [affiliation, setAffiliation] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .listUsers()
      .then(setUsers)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (user?.is_admin) load();
  }, [user, load]);

  if (loading) return <div className="page muted">Loading…</div>;
  if (!user) return <div className="page">Please sign in.</div>;
  if (!user.is_admin) return <div className="page error">Admin access required.</div>;

  const onAdd = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.createUser(email.trim(), {
        name: name.trim(),
        affiliation: affiliation.trim(),
        isAdmin,
      });
      setEmail("");
      setName("");
      setAffiliation("");
      setIsAdmin(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleActive = async (u) => {
    try {
      await api.updateUser(u.id, { is_active: !u.is_active });
      load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <TopMenu />
      <div className="page">
        <div className="row spread" style={{ marginBottom: 16 }}>
          <h2 style={{ margin: 0, color: "var(--text-head)" }}>Users — invite-only allowlist</h2>
        </div>

        {error && <p className="error">{error}</p>}

        <form className="card row" onSubmit={onAdd} style={{ gap: 10, alignItems: "center" }}>
          <input
            type="email"
            placeholder="new.user@temple.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-label="New user email"
            required
          />
          <input
            type="text"
            placeholder="Name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            aria-label="New user name"
          />
          <input
            type="text"
            placeholder="Affiliation (optional)"
            value={affiliation}
            onChange={(e) => setAffiliation(e.target.value)}
            aria-label="New user affiliation"
          />
          <label className="muted">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />{" "}
            admin
          </label>
          <button type="submit">Add user</button>
        </form>

        <div className="card">
          <table className="files">
            <thead>
              <tr>
                <th>Email</th>
                <th>Name</th>
                <th>Affiliation</th>
                <th>Admin</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.email}</td>
                  <td>{u.name || <span className="muted">—</span>}</td>
                  <td>{u.affiliation || <span className="muted">—</span>}</td>
                  <td>{u.is_admin ? "yes" : "no"}</td>
                  <td>
                    <span className={`badge ${u.is_active ? "complete" : "error"}`}>
                      {u.is_active ? "active" : "inactive"}
                    </span>
                  </td>
                  <td>
                    <button className="secondary" onClick={() => toggleActive(u)}>
                      {u.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
