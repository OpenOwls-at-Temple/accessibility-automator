import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the API so no network call happens during the test.
vi.mock("../src/services/api.js", () => ({
  getToken: vi.fn(() => null),
  api: {
    me: vi.fn().mockResolvedValue({ email: "prof@temple.edu", name: "Prof", is_admin: false }),
    devLogin: vi.fn().mockResolvedValue("token"),
    logout: vi.fn(),
  },
}));

import { api } from "../src/services/api.js";
import SignInForm from "../src/components/SignInForm.jsx";
import { AuthProvider } from "../src/hooks/useAuth.jsx";

describe("SignInForm", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the local dev-login field", async () => {
    render(
      <AuthProvider>
        <SignInForm />
      </AuthProvider>
    );
    expect(await screen.findByLabelText("Dev email")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dev sign in/i })).toBeInTheDocument();
  });

  it("submits the entered email to the dev-login API", async () => {
    render(
      <AuthProvider>
        <SignInForm />
      </AuthProvider>
    );
    await userEvent.type(screen.getByLabelText("Dev email"), "prof@temple.edu");
    await userEvent.click(screen.getByRole("button", { name: /dev sign in/i }));
    expect(api.devLogin).toHaveBeenCalledWith("prof@temple.edu");
  });
});
