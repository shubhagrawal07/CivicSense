import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AxiosError } from "axios";
import type { AxiosResponse } from "axios";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getMe, register } from "../api/auth";
import { RegisterPage } from "../pages/RegisterPage";
import { AuthProvider, useAuth } from "./AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";

vi.mock("../api/auth", () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}));

const asha = { id: 1, name: "Asha Rao", email: "asha@example.com", role: "CITIZEN" } as const;

function WhoAmI() {
  const { user, logout } = useAuth();
  return (
    <div>
      <p>{user ? `signed in as ${user.name}` : "signed out"}</p>
      <button onClick={logout}>Log out</button>
    </div>
  );
}

afterEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

describe("auth", () => {
  it("sends a logged-out visitor from a protected page to /login", () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={["/private"]}>
          <Routes>
            <Route path="/login" element={<p>login page</p>} />
            <Route
              path="/private"
              element={
                <ProtectedRoute>
                  <p>secret</p>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </AuthProvider>,
    );

    expect(screen.getByText("login page")).toBeInTheDocument();
    expect(screen.queryByText("secret")).not.toBeInTheDocument();
  });

  it("restores the session from a stored token and forgets it on logout", async () => {
    localStorage.setItem("authToken", "stored-token");
    (getMe as ReturnType<typeof vi.fn>).mockResolvedValue(asha);

    render(
      <AuthProvider>
        <WhoAmI />
      </AuthProvider>,
    );

    expect(await screen.findByText("signed in as Asha Rao")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(screen.getByText("signed out")).toBeInTheDocument();
    expect(localStorage.getItem("authToken")).toBeNull();
  });

  it("shows a server validation error next to the field it belongs to", async () => {
    const response = {
      status: 422,
      data: {
        detail: "Invalid request",
        errors: [{ field: "email", message: "value is not a valid email address" }],
      },
    } as AxiosResponse;
    (register as ReturnType<typeof vi.fn>).mockRejectedValue(
      new AxiosError("bad", "ERR_BAD_REQUEST", undefined, undefined, response),
    );

    render(
      <AuthProvider>
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      </AuthProvider>,
    );

    await userEvent.type(screen.getByLabelText("Name"), "Asha Rao");
    await userEvent.type(screen.getByLabelText("Email"), "asha@example.com");
    await userEvent.type(screen.getByLabelText("Password"), "longenough1");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    const emailField = screen.getByLabelText("Email");
    await waitFor(() => expect(emailField).toHaveAccessibleDescription(/not a valid email/i));
    expect(screen.getByLabelText("Password")).not.toHaveAttribute("aria-invalid");
  });
});
