import { apiRequest } from "./client";
import type { ReferralSummary } from "./types";

export const getReferralSummary = () =>
  apiRequest<ReferralSummary>("/referrals/me");
