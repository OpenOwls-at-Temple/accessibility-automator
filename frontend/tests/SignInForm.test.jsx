import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the API so no network call happens during the test.
vi.mock("../src/services/api.js", () => ({
  api: {
    me: vi.fn().mockRejectedValue(new Error("no session")),
    login: vi
      .fn()
      .mockResolvedValue({ username: "prof", email: "prof@temple.edu", name: "Prof" }),
    logout: vi.fn(),
  },
}));

import { api } from "../src/services/api.js";
import SignInForm from "../src/components/SignInForm.jsx";
import { AuthProvider } from "../src/hooks/useAuth.jsx";

describe("SignInForm", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders the email field and sign-in button", async () => {
    render(
      <AuthProvider>
        <SignInForm />
      </AuthProvider>
    );
    expect(await screen.findByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("submits the entered email to the login API", async () => {
    render(
      <AuthProvider>
        <SignInForm />
      </AuthProvider>
    );
    await userEvent.type(screen.getByLabelText("Email"), "prof@temple.edu");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    expect(api.login).toHaveBeenCalledWith("prof@temple.edu");
  });
});
