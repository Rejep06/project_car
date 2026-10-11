import type {
  DepositInvoice,
  LotterySummary,
  Plan,
  PublicSystemConfig,
  SupportTicket,
  User,
  Wallet,
  Withdrawal,
} from "../api/types";

export const user: User = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "user@example.com",
  pending_email: null,
  email_verified_at: "2026-07-18T10:00:00Z",
  email_verified: true,
  role: "user",
  is_active: true,
  is_frozen: false,
  referral_code: "A1B2C3D4E5F6G7H8",
  referred_by_user_id: null,
  created_at: "2026-07-18T10:00:00Z",
  updated_at: "2026-07-18T10:00:00Z",
};

export const lottery: LotterySummary = {
  id: "99999999-9999-9999-9999-999999999999",
  title: "Розыгрыш автомобиля",
  description: "Публичная лотерея с опубликованными сроками и правилами.",
  cover_image_url: null,
  status: "published",
  ticket_price: "10.000000",
  asset: "USDT",
  sales_start_at: "2026-08-01T10:00:00Z",
  sales_end_at: "2026-09-01T10:00:00Z",
  draw_at: "2026-09-02T10:00:00Z",
  sales_open: true,
  max_tickets_total: 1000,
  max_tickets_per_user: 20,
  tickets_sold: 42,
  confirmed_winners_count: 0,
  created_at: "2026-08-01T10:00:00Z",
  updated_at: "2026-08-01T10:00:00Z",
};

export const plan: Plan = {
  id: "22222222-2222-2222-2222-222222222222",
  title: "Программа Standard",
  tier: "standard",
  short_description: "Прозрачная клиентская программа",
  full_description: "Полное описание условий.",
  image_url: null,
  price: "100.000000",
  asset: "USDT",
  access_duration_value: 6,
  access_duration_unit: "month",
  reward_amount: "5.000000",
  reward_frequency: "weekly",
  reward_duration_value: 3,
  reward_duration_unit: "month",
  is_active: true,
  created_at: "2026-07-18T10:00:00Z",
  updated_at: "2026-07-18T10:00:00Z",
};

export const wallet = (available = "150.000000"): Wallet => ({
  id: "33333333-3333-3333-3333-333333333333",
  asset: "USDT",
  available_balance: available,
  locked_balance: "0.000000",
  updated_at: "2026-07-18T10:00:00Z",
});

export const systemConfig: PublicSystemConfig = {
  app_name: "Automotive Club",
  asset: "USDT",
  network: "Ethereum (ERC-20)",
  min_deposit_amount: "10.000000",
  deposit_invoice_ttl_minutes: 30,
  deposit_amount_reservation_hours: 24,
  min_withdrawal_amount: "20.000000",
  withdrawal_fee_percent: 10,
  withdrawal_is_open: true,
  withdrawal_timezone: "Asia/Almaty",
  withdrawal_weekday_label: "среда",
  next_withdrawal_open_at: null,
  withdrawal_processing_min_hours: 1,
  withdrawal_processing_max_days: 3,
  referral_purchase_bonus_percent: 10,
  premium_referral_reward_bonus: "2.000000",
  support_max_file_size_mb: 5,
  support_max_files_per_message: 3,
};

export function invoice(
  overrides: Partial<DepositInvoice> = {},
): DepositInvoice {
  return {
    id: "44444444-4444-4444-4444-444444444444",
    deposit_wallet_id: "88888888-8888-8888-8888-888888888888",
    wallet_name: "Основной кошелёк",
    asset: "USDT",
    network: "Ethereum (ERC-20)",
    address: `0x${"a".repeat(40)}`,
    requested_amount: "100.000000",
    expected_amount: "100.347000",
    received_amount: null,
    expires_at: "2026-07-18T10:30:00Z",
    amount_reserved_until: "2026-07-19T10:00:00Z",
    status: "waiting",
    credited_at: null,
    credited_after_expiration: false,
    warning: "Отправьте точную сумму",
    created_at: "2026-07-18T10:00:00Z",
    ...overrides,
  };
}

export const withdrawal: Withdrawal = {
  id: "55555555-5555-5555-5555-555555555555",
  asset: "USDT",
  network: "Ethereum (ERC-20)",
  destination_address: `0x${"b".repeat(40)}`,
  amount: "50.000000",
  fee: "2.000000",
  held_total: "52.000000",
  final_total: "52.000000",
  status: "pending_review",
  admin_comment: null,
  txid: null,
  approved_at: null,
  sent_at: null,
  completed_at: null,
  rejected_at: null,
  created_at: "2026-07-18T10:00:00Z",
  updated_at: "2026-07-18T10:00:00Z",
};

export const ticket: SupportTicket = {
  id: "66666666-6666-6666-6666-666666666666",
  user_id: user.id,
  user_email: user.email,
  category: "deposit_problem",
  subject: "Проблема с пополнением",
  status: "open",
  related_deposit_invoice_id: invoice().id,
  txid_conflict: false,
  created_at: "2026-07-18T10:00:00Z",
  updated_at: "2026-07-18T10:00:00Z",
  closed_at: null,
  unread_count: 0,
  messages: [
    {
      id: "77777777-7777-7777-7777-777777777777",
      author_user_id: user.id,
      author_email: user.email,
      message: "Описание",
      txid: `0x${"a".repeat(64)}`,
      created_at: "2026-07-18T10:00:00Z",
      read_at: "2026-07-18T10:00:00Z",
      attachments: [],
    },
  ],
};

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export function errorJson(
  code: string,
  message: string,
  status = 400,
): Response {
  return json({ error: { code, message, details: {} } }, status);
}
