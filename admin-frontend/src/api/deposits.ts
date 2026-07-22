import { apiRequest } from "./client";
import type { Pagination, UnmatchedDeposit } from "./types";
export const listDeposits = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<UnmatchedDeposit>>(
    `/admin/deposits/unmatched?page=${page}&page_size=${pageSize}`,
  );
export const getDeposit = (id: string) =>
  apiRequest<UnmatchedDeposit>(`/admin/deposits/unmatched/${id}`);
export const assignDeposit = (id: string, userId: string, invoiceId?: string) =>
  apiRequest<UnmatchedDeposit>(`/admin/deposits/unmatched/${id}/assign`, {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      ...(invoiceId ? { invoice_id: invoiceId } : {}),
    }),
  });
export const ignoreDeposit = (id: string) =>
  apiRequest<UnmatchedDeposit>(`/admin/deposits/unmatched/${id}/ignore`, {
    method: "POST",
  });
