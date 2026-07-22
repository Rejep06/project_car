import { apiRequest } from "./client";
import type { User } from "./types";

export const getMe = () => apiRequest<User>("/users/me");
export const updateMe = (email: string) =>
  apiRequest<User>("/users/me", {
    method: "PATCH",
    body: JSON.stringify({ email }),
  });
