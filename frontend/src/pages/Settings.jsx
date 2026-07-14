import { useEffect, useState } from "react";
import TopMenu from "../components/TopMenu.jsx";
import { api } from "../services/api.js";
import { useAuth } from "../hooks/useAuth.jsx";

export default function Settings() {
  const { user, loading } = useAuth();
  const [suffix, setSuffix] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      api
        .getSettings()
        .then((s) => setSuffix(s.filename_suffix))
        .catch((err) => setError(err.message));
    }
  }, [user]);

  if (loading) return <div className="page muted">Loading…</div>;
  if (!user) return <div className="page">Please sign in.</div>;

  const onSave = async (e) => {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      const s = await api.updateSettings(suffix.trim());
      setSuffix(s.filename_suffix);
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const preview = `lecture1_${suffix.trim() || "…"}.pptx`;

  return (
    <>
      <TopMenu />
      <div className="page">
        <h2 style={{ marginTop: 0, color: "var(--text-head)" }}>Settings</h2>

        {error && <p className="error">{error}</p>}

        <form className="card" onSubmit={onSave}>
          <label style={{ display: "block", color: "var(--text-head)", fontWeight: 600 }}>
            Remediated filename suffix
          </label>
          <p className="muted" style={{ marginTop: 4 }}>
            Appended to every remediated file&rsquo;s name. Letters, digits, and <code>. _ -</code>{" "}
            only.
          </p>
          <div className="row" style={{ gap: 10, alignItems: "center", marginTop: 8 }}>
            <input
              value={suffix}
              onChange={(e) => {
                setSuffix(e.target.value);
                setSaved(false);
              }}
              aria-label="Remediated filename suffix"
              placeholder="a11y"
            />
            <button type="submit">Save</button>
            {saved && <span className="badge complete">Saved</span>}
          </div>
          <p className="muted" style={{ marginTop: 12 }}>
            Preview: <code>{preview}</code>
          </p>
        </form>

        <p className="muted" style={{ marginTop: 16 }}>
          Changing this affects <strong>future</strong> fixes only — files already remediated keep
          their existing name.
        </p>
      </div>
    </>
  );
}
