import type { DurationUnit, Plan, RewardFrequency } from "../api/types";
import { multiplyMoney } from "./money";

const durationInDays: Record<DurationUnit, number> = {
  day: 1,
  week: 7,
  month: 30,
  year: 365,
};
const frequencyInDays: Record<RewardFrequency, number> = {
  daily: 1,
  weekly: 7,
  monthly: 30,
};

export function estimateRewardCount(
  plan: Pick<
    Plan,
    "reward_duration_value" | "reward_duration_unit" | "reward_frequency"
  >,
): number {
  const days =
    plan.reward_duration_value * durationInDays[plan.reward_duration_unit];
  return Math.max(0, Math.floor(days / frequencyInDays[plan.reward_frequency]));
}

export function estimateRewardTotal(
  plan: Pick<
    Plan,
    | "reward_amount"
    | "reward_duration_value"
    | "reward_duration_unit"
    | "reward_frequency"
  >,
): string {
  return multiplyMoney(plan.reward_amount, estimateRewardCount(plan));
}

export const durationLabels: Record<DurationUnit, string> = {
  day: "дн.",
  week: "нед.",
  month: "мес.",
  year: "г.",
};

export const frequencyLabels: Record<RewardFrequency, string> = {
  daily: "каждый день",
  weekly: "каждую неделю",
  monthly: "каждый месяц",
};
