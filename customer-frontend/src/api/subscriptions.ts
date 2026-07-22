import { apiRequest } from "./client";
import type { Pagination, UserSubscription } from "./types";

export const purchaseSubscription = (planId: string, idempotencyKey: string) =>
  apiRequest<UserSubscription>(`/subscriptions/${planId}/purchase`, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
  });
export const listSubscriptions = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<UserSubscription>>(
    `/subscriptions?page=${page}&page_size=${pageSize}`,
  );
export const getSubscription = (id: string) =>
  apiRequest<UserSubscription>(`/subscriptions/${id}`);
