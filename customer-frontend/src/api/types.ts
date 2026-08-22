export type UserRole = "user" | "admin";
export type DurationUnit = "day" | "week" | "month" | "year";
export type RewardFrequency = "daily" | "weekly" | "monthly";
export type PlanTier = "starter" | "standard" | "premium";

export interface Pagination<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface User {
  id: string;
  email: string;
  pending_email: string | null;
  email_verified_at: string | null;
  email_verified: boolean;
  role: UserRole;
  is_active: boolean;
  is_frozen: boolean;
  referral_code: string;
  referred_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Plan {
  id: string;
  title: string;
  tier: PlanTier;
  short_description: string;
  full_description: string;
  image_url: string | null;
  price: string;
  asset: string;
  access_duration_value: number;
  access_duration_unit: DurationUnit;
  reward_amount: string;
  reward_frequency: RewardFrequency;
  reward_duration_value: number;
  reward_duration_unit: DurationUnit;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Wallet {
  id: string;
  asset: string;
  available_balance: string;
  locked_balance: string;
  updated_at: string;
}

export interface WalletTransaction {
  id: string;
  operation_type:
    | "deposit_credit"
    | "program_purchase"
    | "reward_credit"
    | "referral_purchase_bonus"
    | "referral_reward_bonus"
    | "withdrawal_hold"
    | "withdrawal_complete"
    | "withdrawal_refund"
    | "admin_adjustment"
    | "lottery_ticket_purchase"
    | "lottery_prize_credit"
    | "lottery_ticket_refund";
  available_delta: string;
  locked_delta: string;
  available_after: string;
  locked_after: string;
  description: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  created_at: string;
}

export interface DepositWallet {
  id: string;
  title: string;
  address: string;
  asset: string;
  network: string;
  network_display_name: string;
  sort_order: number;
  is_active: boolean;
}

export interface DepositInvoice {
  id: string;
  deposit_wallet_id: string | null;
  wallet_name: string;
  asset: string;
  network: string;
  address: string;
  requested_amount: string;
  expected_amount: string;
  received_amount: string | null;
  expires_at: string;
  amount_reserved_until: string;
  status:
    | "waiting"
    | "detected"
    | "credited"
    | "expired"
    | "manual_review"
    | "cancelled";
  credited_at: string | null;
  credited_after_expiration: boolean;
  warning: string;
  created_at: string;
}

export interface Withdrawal {
  id: string;
  asset: string;
  network: string;
  destination_address: string;
  amount: string;
  fee: string;
  held_total: string;
  final_total: string;
  status:
    | "pending_review"
    | "approved"
    | "sent"
    | "completed"
    | "rejected"
    | "cancelled";
  admin_comment: string | null;
  txid: string | null;
  approved_at: string | null;
  sent_at: string | null;
  completed_at: string | null;
  rejected_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RewardPayout {
  id: string;
  amount: string;
  asset: string;
  due_at: string;
  paid_at: string | null;
  status: "pending" | "processing" | "paid" | "failed" | "cancelled";
  attempt_count: number;
}

export interface UserSubscription {
  id: string;
  plan_id: string;
  plan_title: string;
  plan_tier: PlanTier;
  status: "active" | "expired" | "cancelled";
  purchased_at: string;
  access_started_at: string;
  access_ends_at: string;
  price: string;
  reward_amount: string;
  reward_frequency: RewardFrequency;
  reward_duration_value: number;
  reward_duration_unit: DurationUnit;
  reward_payouts: RewardPayout[];
}

export interface Post {
  id: string;
  author_id: string;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  cover_image_url: string | null;
  status: "draft" | "published" | "archived";
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
  download_url: string;
}

export interface SupportMessage {
  id: string;
  author_user_id: string;
  author_email: string;
  message: string;
  txid: string | null;
  created_at: string;
  attachments: Attachment[];
}

export interface SupportTicket {
  id: string;
  user_id: string;
  user_email: string;
  category:
    | "deposit_problem"
    | "withdrawal_problem"
    | "subscription_problem"
    | "other";
  subject: string;
  status: "open" | "in_review" | "waiting_user" | "resolved" | "closed";
  related_deposit_invoice_id: string | null;
  txid_conflict: boolean;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  messages: SupportMessage[];
}

export interface PublicSystemConfig {
  app_name: string;
  asset: string;
  network: string;
  min_deposit_amount: string;
  deposit_invoice_ttl_minutes: number;
  deposit_amount_reservation_hours: number;
  min_withdrawal_amount: string;
  withdrawal_fee: string;
  withdrawal_is_open: boolean;
  withdrawal_timezone: string;
  withdrawal_weekday_label: string;
  next_withdrawal_open_at: string | null;
  withdrawal_processing_min_hours: number;
  withdrawal_processing_max_days: number;
  referral_purchase_bonus_percent: number;
  premium_referral_reward_bonus: string;
  support_max_file_size_mb: number;
  support_max_files_per_message: number;
}

export interface ReferralMember {
  email: string;
  joined_at: string;
  has_program: boolean;
}

export interface ReferralSummary {
  referral_code: string;
  invited_count: number;
  active_invited_count: number;
  total_earned: string;
  purchase_bonus_earned: string;
  reward_bonus_earned: string;
  purchase_bonus_percent: number;
  premium_reward_bonus: string;
  members: ReferralMember[];
}


export interface RegistrationResponse {
  email: string;
  verification_required: boolean;
  message: string;
  debug_verification_token: string | null;
}

export type LotteryStatus =
  | "draft"
  | "published"
  | "awaiting_confirmation"
  | "completed"
  | "cancelled";
export type LotteryPrizeType = "balance" | "physical";
export type LotteryTicketStatus = "active" | "refunded";
export type LotteryWinnerStatus = "pending" | "confirmed" | "cancelled";

export interface LotteryPrize {
  id: string;
  title: string;
  description: string;
  prize_type: LotteryPrizeType;
  amount: string | null;
  asset: string;
  quantity: number;
  sort_order: number;
  image_url: string | null;
  manager_telegram: string | null;
  created_at: string;
  updated_at: string;
}

export interface LotteryWinnerPublic {
  id: string;
  prize_id: string;
  prize_title: string;
  ticket_code: string;
  winner_email_masked: string;
  confirmed_at: string;
}

export interface LotterySummary {
  id: string;
  title: string;
  description: string;
  cover_image_url: string | null;
  status: LotteryStatus;
  ticket_price: string;
  asset: string;
  sales_start_at: string;
  sales_end_at: string;
  draw_at: string;
  sales_open: boolean;
  max_tickets_total: number | null;
  max_tickets_per_user: number;
  tickets_sold: number;
  confirmed_winners_count: number;
  created_at: string;
  updated_at: string;
}

export interface LotteryDetail extends LotterySummary {
  manager_telegram: string | null;
  rules_text: string;
  rules_version: string;
  prizes: LotteryPrize[];
  winners: LotteryWinnerPublic[];
}

export interface LotteryTicket {
  id: string;
  lottery_id: string;
  lottery_title: string;
  ticket_code: string;
  price: string;
  asset: string;
  status: LotteryTicketStatus;
  purchased_at: string;
  draw_at: string;
  winner_status: LotteryWinnerStatus | null;
  prize_title: string | null;
  prize_type: LotteryPrizeType | null;
  prize_amount: string | null;
  claim_contact: string | null;
}

export interface LotteryPurchase {
  purchase_id: string;
  lottery_id: string;
  quantity: number;
  total_amount: string;
  asset: string;
  tickets: LotteryTicket[];
  created_at: string;
}

export interface UserNotification {
  id: string;
  notification_type: "lottery_win" | "system";
  title: string;
  message: string;
  action_url: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}
