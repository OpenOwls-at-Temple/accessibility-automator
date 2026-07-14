// Thin client for the Accessibility Automator backend.
// Auth is a JWT bearer token kept in localStorage and sent as `Authorization`.

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API = `${BASE}/api/v1`;
const TOKEN_KEY = "a11y_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function fail(res) {
  const body = await res.json().catch(() => ({ detail: res.statusText }));
  const error = new Error(body.detail || `HTTP ${res.status}`);
  error.status = res.status;
  return error;
}

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: authHeaders({ "Content-Type": "application/json", ...(options.headers || {}) }),
  });
  if (!res.ok) throw await fail(res);
  return res.status === 204 ? null : res.json();
}

export const api = {
  base: BASE,

  // --- auth ---
  ssoLogin: async (credential) => {
    const { access_token } = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ credential }),
    });
    setToken(access_token);
    return access_token;
  },
  devLogin: async (email) => {
    const { access_token } = await request("/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
    setToken(access_token);
    return access_token;
  },
  me: () => request("/auth/me"),
  logout: () => clearToken(),

  // --- workspace ---
  listGroups: () => request("/groups"),
  getGroup: (group) => request(`/groups/${encodeURIComponent(group)}`),
  remediate: (group, files = null) =>
    request(`/groups/${encodeURIComponent(group)}/remediate`, {
      method: "POST",
      body: JSON.stringify({ files }),
    }),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getReport: (group, name) =>
    request(`/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/report`),
  scanFile: (group, name) =>
    request(`/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/scan`, {
      method: "POST",
    }),
  applyReview: (group, name, suggestions) =>
    request(`/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/apply-review`, {
      method: "POST",
      body: JSON.stringify({ suggestions }),
    }),
  signoff: (group, name, checkId, note = null) =>
    request(`/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/signoff`, {
      method: "POST",
      body: JSON.stringify({ check_id: checkId, note }),
    }),

  uploadFiles: async (group, fileList) => {
    const form = new FormData();
    for (const file of fileList) form.append("files", file);
    // No Content-Type header — the browser sets the multipart boundary.
    const res = await fetch(`${API}/groups/${encodeURIComponent(group)}/files`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });
    if (!res.ok) throw await fail(res);
    return res.json();
  },

  // Authed file download: a plain <a href> can't send the bearer token, so we
  // fetch with the header, then save the blob via a temporary object URL.
  download: async (group, name, kind) => {
    const res = await fetch(
      `${API}/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/download?kind=${kind}`,
      { headers: authHeaders() }
    );
    if (!res.ok) throw await fail(res);
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    // Fall back to a deterministic name if the header is unreadable — the
    // remediated file should keep its `_a11y` suffix, not the original name.
    const fallback = kind === "output" ? name.replace(/\.([^.]+)$/, "_a11y.$1") : name;
    const filename = match ? match[1] : fallback;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  // --- admin (invite-only allowlist) ---
  listUsers: () => request("/admin/users"),
  createUser: (email, isAdmin = false) =>
    request("/admin/users", {
      method: "POST",
      body: JSON.stringify({ email, is_admin: isAdmin }),
    }),
  updateUser: (id, patch) =>
    request(`/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
};
