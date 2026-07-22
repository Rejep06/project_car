import { apiRequest } from "./client";
import type {
  DepositInvoice,
  Pagination,
  Wallet,
  WalletTransaction,
  Withdrawal,
} from "./types";

export const getWallet = () => apiRequest<Wallet>("/wallet");
export const listTransactions = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<WalletTransaction>>(
    `/wallet/transactions?page=${page}&page_size=${pageSize}`,
  );
export const createDeposit = (amount: string) =>
  apiRequest<DepositInvoice>("/wallet/deposits", {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
export const listDeposits = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<DepositInvoice>>(
    `/wallet/deposits?page=${page}&page_size=${pageSize}`,
  );
export const getDeposit = (id: string) =>
  apiRequest<DepositInvoice>(`/wallet/deposits/${id}`);
export const createWithdrawal = (destinationAddress: string, amount: string) =>
  apiRequest<Withdrawal>("/wallet/withdrawals", {
    method: "POST",
    body: JSON.stringify({ destination_address: destinationAddress, amount }),
  });
export const listWithdrawals = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<Withdrawal>>(
    `/wallet/withdrawals?page=${page}&page_size=${pageSize}`,
  );
export const getWithdrawal = (id: string) =>
  apiRequest<Withdrawal>(`/wallet/withdrawals/${id}`);
export const cancelWithdrawal = (id: string) =>
  apiRequest<Withdrawal>(`/wallet/withdrawals/${id}/cancel`, {
    method: "POST",
  });
