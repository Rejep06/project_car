import { apiRequest } from "./client";
import type { TokenPair, User } from "./types";

export function register(email: string, password: string) {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  });
}

export function login(email: string, password: string) {
  return apiRequest<TokenPair>("/auth/login", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  });
}

export function logout(refreshToken: string) {
  return apiRequest<{ message: string }>("/auth/logout", {
    method: "POST",
    skipAuth: true,
    skipRefresh: true,
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}
