import { apiRequest } from "./client";
import type { RegistrationResponse, TokenPair } from "./types";

export interface RegistrationConsents {
  accept_terms: true;
  accept_privacy_policy: true;
  accept_personal_data_processing: true;
  accept_program_rules: true;
  confirm_age_18: true;
}

export function register(
  email: string,
  password: string,
  consents: RegistrationConsents,
  referralCode?: string,
) {
  return apiRequest<RegistrationResponse>("/auth/register", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({
      email,
      password,
      referral_code: referralCode || undefined,
      ...consents,
    }),
  });
}

export function confirmEmail(token: string) {
  return apiRequest<{ message: string; email: string | null }>(
    "/auth/email-verification/confirm",
    {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ token }),
    },
  );
}

export function resendEmailVerification(email: string) {
  return apiRequest<{ message: string; email: string | null }>(
    "/auth/email-verification/resend",
    {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ email }),
    },
  );
}

export function requestPasswordReset(email: string) {
  return apiRequest<{ message: string }>("/auth/password-reset/request", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(token: string, newPassword: string) {
  return apiRequest<{ message: string; email: string | null }>(
    "/auth/password-reset/confirm",
    {
      method: "POST",
      skipAuth: true,
      body: JSON.stringify({ token, new_password: newPassword }),
    },
  );
}

export function login(email: string, password: string) {
  return apiRequest<TokenPair>("/auth/login", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email, password }),
  });
}

export function logout(refreshToken: string) {
  return apiRequest<{ message: string }>("/auth/logout", {
    method: "POST",
    skipAuth: true,
    skipRefresh: true,
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}
