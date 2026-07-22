import { apiRequest } from "./client";
import type { Pagination, Plan } from "./types";

export const listPlans = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<Plan>>(`/plans?page=${page}&page_size=${pageSize}`, {
    skipAuth: true,
  });
export const getPlan = (slug: string) =>
  apiRequest<Plan>(`/plans/${encodeURIComponent(slug)}`, { skipAuth: true });
