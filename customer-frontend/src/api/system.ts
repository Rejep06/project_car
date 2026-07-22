import { apiRequest } from "./client";
import type { PublicSystemConfig } from "./types";

let cached: PublicSystemConfig | null = null;
export async function getSystemConfig(): Promise<PublicSystemConfig> {
  if (cached) return cached;
  cached = await apiRequest<PublicSystemConfig>("/system/config", {
    skipAuth: true,
  });
  return cached;
}
