import { apiRequest } from "./client";
import type { Pagination, Plan, PlanInput } from "./types";
export const listPlans = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<Plan>>(
    `/admin/plans?page=${page}&page_size=${pageSize}`,
  );
export const getPlan = (id: string) => apiRequest<Plan>(`/admin/plans/${id}`);
export const createPlan = (data: PlanInput) =>
  apiRequest<Plan>("/admin/plans", {
    method: "POST",
    body: JSON.stringify(data),
  });
export const updatePlan = (id: string, data: Partial<PlanInput>) =>
  apiRequest<Plan>(`/admin/plans/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
export const activatePlan = (id: string) =>
  apiRequest<Plan>(`/admin/plans/${id}/activate`, { method: "POST" });
export const deactivatePlan = (id: string) =>
  apiRequest<Plan>(`/admin/plans/${id}/deactivate`, { method: "POST" });
