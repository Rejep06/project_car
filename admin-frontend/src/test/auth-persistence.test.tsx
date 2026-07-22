import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { tokenStore } from "../auth/tokenStore";
import { admin } from "./fixtures";
import { json } from "./helpers";

function SessionProbe() {
  const { user, loading } = useAuth();
  if (loading) return <div>loading</div>;
  return <div>{user?.email ?? "guest"}</div>;
}

describe("сохранение административной сессии", () => {
  it("восстанавливает вход администратора после обновления страницы", async () => {
    tokenStore.setTokens("saved-admin-access", "saved-admin-refresh");

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/users/me")) {
          const headers = new Headers(init?.headers);
          expect(headers.get("Authorization")).toBe(
            "Bearer saved-admin-access",
          );
          return json(admin);
        }
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    expect(await screen.findByText(admin.email)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).endsWith("/auth/refresh"),
      ),
    ).toBe(false);
    expect(tokenStore.getAccessToken()).toBe("saved-admin-access");
    expect(tokenStore.getRefreshToken()).toBe("saved-admin-refresh");
  });
});
