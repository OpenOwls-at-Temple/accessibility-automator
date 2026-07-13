// Auth context: tracks the signed-in user and exposes sign-in/out.
// On mount, if a JWT is stored it validates it via GET /auth/me.

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api.me());
    } catch {
      api.logout();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const ssoLogin = async (credential) => {
    await api.ssoLogin(credential);
    setUser(await api.me());
  };

  const devLogin = async (email) => {
    await api.devLogin(email);
    setUser(await api.me());
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, ssoLogin, devLogin, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
