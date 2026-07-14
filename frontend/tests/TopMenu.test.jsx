import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../src/services/api.js", () => ({
  getToken: vi.fn(() => "token"),
  api: {
    me: vi.fn(),
    logout: vi.fn(),
  },
}));

import { api } from "../src/services/api.js";
import TopMenu from "../src/components/TopMenu.jsx";
import { AuthProvider } from "../src/hooks/useAuth.jsx";

function renderMenu() {
  render(
    <MemoryRouter>
      <AuthProvider>
        <TopMenu />
      </AuthProvider>
    </MemoryRouter>
  );
}

describe("TopMenu", () => {
  beforeEach(() => vi.clearAllMocks());

  it("always shows Workspace, Settings, and Sign out", async () => {
    api.me.mockResolvedValue({ email: "prof@temple.edu", name: "Prof", is_admin: false });
    renderMenu();
    expect(await screen.findByRole("link", { name: "Workspace" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Settings" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("hides Manage users for non-admins", async () => {
    api.me.mockResolvedValue({ email: "prof@temple.edu", is_admin: false });
    renderMenu();
    await screen.findByRole("link", { name: "Settings" });
    expect(screen.queryByRole("link", { name: /manage users/i })).not.toBeInTheDocument();
  });

  it("shows Manage users for admins", async () => {
    api.me.mockResolvedValue({ email: "admin@temple.edu", is_admin: true });
    renderMenu();
    expect(await screen.findByRole("link", { name: /manage users/i })).toBeInTheDocument();
  });
});
