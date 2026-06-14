// Thin client for the Accessibility Automator backend.
// All requests send the auth cookie (credentials: "include"); the backend's
// CORS config allows this origin with credentials.

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API = `${BASE}/api/v1`;

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const error = new Error(body.detail || `HTTP ${res.status}`);
    error.status = res.status;
    throw error;
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  base: BASE,

  login: (email) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email }) }),
  me: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),

  listGroups: () => request("/groups"),
  getGroup: (group) => request(`/groups/${encodeURIComponent(group)}`),
  remediate: (group, files = null) =>
    request(`/groups/${encodeURIComponent(group)}/remediate`, {
      method: "POST",
      body: JSON.stringify({ files }),
    }),
  getJob: (jobId) => request(`/jobs/${jobId}`),
  getReport: (group, name) =>
    request(
      `/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/report`
    ),
  signoff: (group, name, checkId, note = null) =>
    request(
      `/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(name)}/signoff`,
      { method: "POST", body: JSON.stringify({ check_id: checkId, note }) }
    ),

  uploadFiles: async (group, fileList) => {
    const form = new FormData();
    for (const file of fileList) form.append("files", file);
    // No Content-Type header — the browser sets the multipart boundary.
    const res = await fetch(`${API}/groups/${encodeURIComponent(group)}/files`, {
      method: "POST",
      credentials: "include",
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },

  downloadUrl: (group, name, kind) =>
    `${API}/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(
      name
    )}/download?kind=${kind}`,
  reportHtmlUrl: (group, name) =>
    `${API}/groups/${encodeURIComponent(group)}/files/${encodeURIComponent(
      name
    )}/report/html`,
};
