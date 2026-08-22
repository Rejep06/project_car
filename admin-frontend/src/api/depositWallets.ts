import { apiRequest } from "./client";
import type {
  DepositWallet,
  DepositWalletInput,
  Pagination,
} from "./types";

export const listDepositWallets = (page = 1, pageSize = 50) =>
  apiRequest<Pagination<DepositWallet>>(
    `/admin/deposit-wallets?page=${page}&page_size=${pageSize}`,
  );

export const createDepositWallet = (data: DepositWalletInput) =>
  apiRequest<DepositWallet>("/admin/deposit-wallets", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateDepositWallet = (
  id: string,
  data: Partial<DepositWalletInput>,
) =>
  apiRequest<DepositWallet>(`/admin/deposit-wallets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
