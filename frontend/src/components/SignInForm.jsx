import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth.jsx";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

// Sign-in is invite-only: Google verifies identity, the backend allowlist
// decides access. A local-only dev login (shown under `import.meta.env.DEV`)
// skips Google but still requires a registered account.
export default function SignInForm() {
  const { ssoLogin, devLogin } = useAuth();
  const [devEmail, setDevEmail] = useState("");
  const [error, setError] = useState("");
  const btnRef = useRef(null);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return undefined;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    script.onload = () => {
      if (!window.google || !btnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async ({ credential }) => {
          setError("");
          try {
            await ssoLogin(credential);
          } catch (err) {
            setError(err.message);
          }
        },
      });
      window.google.accounts.id.renderButton(btnRef.current, {
        theme: "outline",
        size: "large",
        text: "signin_with",
        width: 320,
      });
    };

    return () => {
      if (document.body.contains(script)) document.body.removeChild(script);
    };
  }, [ssoLogin]);

  const onDevLogin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await devLogin(devEmail.trim());
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="signin">
      <h1>🦉 Accessibility Automator</h1>
      <p className="muted">
        Sign in with your Temple Google account to remediate your lecture materials.
      </p>
      {error && <p className="error">{error}</p>}
      {GOOGLE_CLIENT_ID ? (
        <div className="google-signin" ref={btnRef} />
      ) : (
        <p className="error">
          Google sign-in is not configured (VITE_GOOGLE_CLIENT_ID is missing).
        </p>
      )}
      <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
        Access is invite-only — an administrator must add your Temple account.
      </p>
      {import.meta.env.DEV && (
        <form className="dev-login" onSubmit={onDevLogin} style={{ marginTop: 24 }}>
          <h2 style={{ fontSize: 15, color: "var(--text-head)" }}>Local dev login</h2>
          <input
            type="email"
            placeholder="registered email"
            value={devEmail}
            onChange={(e) => setDevEmail(e.target.value)}
            aria-label="Dev email"
            required
          />
          <button type="submit">Dev sign in</button>
        </form>
      )}
    </div>
  );
}
