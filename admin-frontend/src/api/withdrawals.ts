import { apiRequest } from "./client";
import type { AdminWithdrawal, Pagination } from "./types";
export const listWithdrawals = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<AdminWithdrawal>>(
    `/admin/withdrawals?page=${page}&page_size=${pageSize}`,
  );
export const getWithdrawal = (id: string) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}`);

export interface WithdrawalAmountsUpdate {
  amount: string;
  fee: string;
  comment: string;
  expected_updated_at: string;
}

export const updateWithdrawalAmounts = (
  id: string,
  data: WithdrawalAmountsUpdate,
  idempotencyKey: string,
) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}/amounts`, {
    method: "PATCH",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(data),
  });

export const getWithdrawalFeeConfig = () =>
  apiRequest<{ withdrawal_fee_percent: number }>("/system/config");

export const approveWithdrawal = (id: string) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}/approve`, {
    method: "POST",
  });
export const rejectWithdrawal = (id: string, comment: string) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ comment }),
  });
export const markSent = (
  id: string,
  txid: string,
  actual_fee: string,
  comment?: string,
) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}/mark-sent`, {
    method: "POST",
    body: JSON.stringify({ txid, actual_fee, comment: comment || null }),
  });
export const completeWithdrawal = (id: string, comment?: string) =>
  apiRequest<AdminWithdrawal>(`/admin/withdrawals/${id}/complete`, {
    method: "POST",
    body: JSON.stringify({ comment: comment || null }),
  });
