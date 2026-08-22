import { apiRequest } from "./client";
import type {
  LotteryAdmin,
  LotteryAdminTicket,
  LotteryInput,
  LotteryPrize,
  LotteryPrizeInput,
  LotterySummary,
  LotteryWinnerAdmin,
  Pagination,
} from "./types";

export const listLotteries = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<LotterySummary>>(
    `/admin/lotteries?page=${page}&page_size=${pageSize}`,
  );

export const getLottery = (id: string) =>
  apiRequest<LotteryAdmin>(`/admin/lotteries/${id}`);

export const createLottery = (data: LotteryInput) =>
  apiRequest<LotteryAdmin>("/admin/lotteries", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateLottery = (id: string, data: Partial<LotteryInput>) =>
  apiRequest<LotteryAdmin>(`/admin/lotteries/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const publishLottery = (id: string) =>
  apiRequest<LotteryAdmin>(`/admin/lotteries/${id}/publish`, {
    method: "POST",
  });

export const createLotteryPrize = (lotteryId: string, data: LotteryPrizeInput) =>
  apiRequest<LotteryPrize>(`/admin/lotteries/${lotteryId}/prizes`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateLotteryPrize = (
  lotteryId: string,
  prizeId: string,
  data: Partial<LotteryPrizeInput>,
) =>
  apiRequest<LotteryPrize>(
    `/admin/lotteries/${lotteryId}/prizes/${prizeId}`,
    { method: "PATCH", body: JSON.stringify(data) },
  );

export const deleteLotteryPrize = (lotteryId: string, prizeId: string) =>
  apiRequest<{ message: string }>(
    `/admin/lotteries/${lotteryId}/prizes/${prizeId}`,
    { method: "DELETE" },
  );

export const listLotteryTickets = (
  lotteryId: string,
  page = 1,
  pageSize = 100,
  search = "",
) => {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (search.trim()) query.set("search", search.trim());
  return apiRequest<Pagination<LotteryAdminTicket>>(
    `/admin/lotteries/${lotteryId}/tickets?${query.toString()}`,
  );
};

export const drawLotteryRandom = (lotteryId: string) =>
  apiRequest<LotteryWinnerAdmin[]>(
    `/admin/lotteries/${lotteryId}/draw-random`,
    { method: "POST" },
  );

export const selectLotteryWinnerManually = (
  lotteryId: string,
  prizeId: string,
  ticketId: string,
) =>
  apiRequest<LotteryWinnerAdmin>(
    `/admin/lotteries/${lotteryId}/winners/manual`,
    {
      method: "POST",
      body: JSON.stringify({ prize_id: prizeId, ticket_id: ticketId }),
    },
  );

export const removeLotteryWinner = (winnerId: string) =>
  apiRequest<{ message: string }>(`/admin/lotteries/winners/${winnerId}`, {
    method: "DELETE",
  });

export const confirmLotteryWinner = (winnerId: string, note?: string) =>
  apiRequest<LotteryWinnerAdmin>(
    `/admin/lotteries/winners/${winnerId}/confirm`,
    { method: "POST", body: JSON.stringify({ note: note || null }) },
  );

export const confirmAllLotteryWinners = (lotteryId: string) =>
  apiRequest<LotteryWinnerAdmin[]>(
    `/admin/lotteries/${lotteryId}/winners/confirm-all`,
    { method: "POST" },
  );
