import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { tokenStore } from "../auth/tokenStore";
import { json, user } from "./fixtures";

function SessionProbe() {
  const { user: currentUser, loading } = useAuth();
  if (loading) return <div>loading</div>;
  return <div>{currentUser?.email ?? "guest"}</div>;
}

function renderSession() {
  return render(
    <AuthProvider>
      <SessionProbe />
    </AuthProvider>,
  );
}

describe("сохранение клиентской сессии", () => {
  it("восстанавливает вход после обновления страницы по сохранённому access token", async () => {
    tokenStore.setTokens("saved-access", "saved-refresh");

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/users/me")) {
          const headers = new Headers(init?.headers);
          expect(headers.get("Authorization")).toBe("Bearer saved-access");
          return json(user);
        }
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    renderSession();

    expect(await screen.findByText(user.email)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([url]) =>
        String(url).endsWith("/auth/refresh"),
      ),
    ).toBe(false);
    expect(tokenStore.getAccessToken()).toBe("saved-access");
    expect(tokenStore.getRefreshToken()).toBe("saved-refresh");
  });

  it("обновляет истёкший access token и сохраняет новую пару токенов", async () => {
    tokenStore.setTokens("expired-access", "saved-refresh");
    let meRequests = 0;

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);

        if (path.endsWith("/users/me")) {
          meRequests += 1;
          const headers = new Headers(init?.headers);
          if (meRequests === 1) {
            expect(headers.get("Authorization")).toBe(
              "Bearer expired-access",
            );
            return json(
              { error: { code: "token_expired", message: "Token expired" } },
              401,
            );
          }
          expect(headers.get("Authorization")).toBe("Bearer renewed-access");
          return json(user);
        }

        if (path.endsWith("/auth/refresh")) {
          expect(JSON.parse(String(init?.body))).toEqual({
            refresh_token: "saved-refresh",
          });
          return json({
            access_token: "renewed-access",
            refresh_token: "renewed-refresh",
            token_type: "bearer",
            expires_in: 900,
          });
        }

        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    renderSession();

    expect(await screen.findByText(user.email)).toBeInTheDocument();
    expect(meRequests).toBe(2);
    expect(tokenStore.getAccessToken()).toBe("renewed-access");
    expect(tokenStore.getRefreshToken()).toBe("renewed-refresh");
  });
});
