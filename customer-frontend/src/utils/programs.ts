import type { PlanTier } from "../api/types";

export const planTierLabels: Record<PlanTier, string> = {
  starter: "Старт",
  standard: "Стандарт",
  premium: "Премиум",
};

export const planTierOrder: Record<PlanTier, number> = {
  starter: 0,
  standard: 1,
  premium: 2,
};
