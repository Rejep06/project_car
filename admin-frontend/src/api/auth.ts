import { apiRequest } from "./client";
import type { TokenPair } from "./types";
export const login = (email: string, password: string) =>
  apiRequest<TokenPair>("/auth/login", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  });
export const logout = (refresh_token: string) =>
  apiRequest<{ message: string }>("/auth/logout", {
    method: "POST",
    skipAuth: true,
    skipRefresh: true,
    body: JSON.stringify({ refresh_token }),
  });
