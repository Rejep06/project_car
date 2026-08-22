import { apiRequest } from "./client";
import type {
  LotteryDetail,
  LotteryPurchase,
  LotterySummary,
  LotteryTicket,
  Pagination,
} from "./types";

export function listLotteries(page = 1, pageSize = 12) {
  return apiRequest<Pagination<LotterySummary>>(
    `/lotteries?page=${page}&page_size=${pageSize}`,
    { skipAuth: true },
  );
}

export function getLottery(id: string) {
  return apiRequest<LotteryDetail>(`/lotteries/${id}`, { skipAuth: true });
}

export function getMyLotteryTickets(id: string) {
  return apiRequest<LotteryTicket[]>(`/lotteries/${id}/my-tickets`);
}

export function listMyLotteryTickets(page = 1, pageSize = 20) {
  return apiRequest<Pagination<LotteryTicket>>(
    `/lotteries/me/tickets?page=${page}&page_size=${pageSize}`,
  );
}

export function buyLotteryTickets(
  lotteryId: string,
  quantity: number,
  idempotencyKey: string,
) {
  return apiRequest<LotteryPurchase>(`/lotteries/${lotteryId}/tickets`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify({ quantity, accept_rules: true }),
  });
}
