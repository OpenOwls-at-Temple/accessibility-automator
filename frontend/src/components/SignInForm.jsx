import { useState } from "react";
import { useAuth } from "../hooks/useAuth.jsx";

export default function SignInForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="signin">
      <h1>🦉 Accessibility Automator</h1>
      <p className="muted">
        Sign in with your Temple email to remediate your lecture materials.
      </p>
      <form onSubmit={onSubmit}>
        <input
          type="email"
          placeholder="you@temple.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          aria-label="Email"
          required
        />
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      <p className="muted" style={{ marginTop: 24, fontSize: 13 }}>
        Dev mode: any email signs you into a private workspace.
      </p>
    </div>
  );
}
