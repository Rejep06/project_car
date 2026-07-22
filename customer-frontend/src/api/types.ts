export type UserRole = "user" | "admin";
export type DurationUnit = "day" | "week" | "month" | "year";
export type RewardFrequency = "daily" | "weekly" | "monthly";

export interface Pagination<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  is_frozen: boolean;
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
  slug: string;
  category: "game" | "application";
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
    | "subscription_purchase"
    | "reward_credit"
    | "withdrawal_hold"
    | "withdrawal_complete"
    | "withdrawal_refund"
    | "admin_adjustment";
  available_delta: string;
  locked_delta: string;
  available_after: string;
  locked_after: string;
  description: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  created_at: string;
}

export interface DepositInvoice {
  id: string;
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
  support_max_file_size_mb: number;
  support_max_files_per_message: number;
}
