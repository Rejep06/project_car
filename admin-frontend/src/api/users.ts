import { apiRequest } from "./client";
import type { AdminUser, Pagination, User } from "./types";
export const getMe = () => apiRequest<User>("/users/me");
export const listUsers = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<AdminUser>>(
    `/admin/users?page=${page}&page_size=${pageSize}`,
  );
export const getUser = (id: string) =>
  apiRequest<AdminUser>(`/admin/users/${id}`);
export const freezeUser = (id: string) =>
  apiRequest<AdminUser>(`/admin/users/${id}/freeze`, { method: "POST" });
export const unfreezeUser = (id: string) =>
  apiRequest<AdminUser>(`/admin/users/${id}/unfreeze`, { method: "POST" });
export const adjustBalance = (
  id: string,
  amount: string,
  description: string,
  key: string,
) =>
  apiRequest<AdminUser>(`/admin/users/${id}/balance-adjustment`, {
    method: "POST",
    headers: { "Idempotency-Key": key },
    body: JSON.stringify({ amount, description }),
  });
