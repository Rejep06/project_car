export interface Pagination<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
export interface User {
  id: string;
  email: string;
  role: "user" | "admin";
  is_active: boolean;
  is_frozen: boolean;
  created_at: string;
  updated_at: string;
}
export interface AdminUser extends User {
  available_balance: string;
  locked_balance: string;
  asset: string;
}
export type DurationUnit = "day" | "week" | "month" | "year";
export type RewardFrequency = "daily" | "weekly" | "monthly";
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
export interface PlanInput {
  title: string;
  slug: string;
  category: "game" | "application";
  short_description: string;
  full_description: string;
  image_url: string | null;
  price: string;
  access_duration_value: number;
  access_duration_unit: DurationUnit;
  reward_amount: string;
  reward_frequency: RewardFrequency;
  reward_duration_value: number;
  reward_duration_unit: DurationUnit;
  is_active?: boolean;
}
export interface UnmatchedDeposit {
  id: string;
  binance_record_id: string;
  binance_deposit_id: string;
  txid: string;
  coin: string;
  amount: string;
  address: string;
  network: string;
  binance_status: "pending" | "success" | "failed";
  deposit_time: string;
  credited_at: string | null;
  txid_already_used: boolean;
  reason:
    | "wrong_amount"
    | "expired_invoice"
    | "invoice_not_found"
    | "duplicate_candidate"
    | "unknown";
  status: "unresolved" | "assigned" | "ignored";
  assigned_user_id: string | null;
  assigned_invoice_id: string | null;
  assigned_at: string | null;
  created_at: string;
}
export interface AdminWithdrawal {
  id: string;
  user_id: string;
  user_email: string;
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
export interface AdminTicket {
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
  expected_amount: string | null;
  actual_amount: string | null;
  binance_deposit_id: string | null;
  binance_txid: string | null;
  binance_address: string | null;
  binance_network: string | null;
  binance_status: string | null;
  binance_detected_at: string | null;
  binance_raw_data: Record<string, unknown> | null;
  txid_already_used: boolean;
  warning: string | null;
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
export interface PostInput {
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  cover_image_url: string | null;
}
export interface AuditLog {
  id: string;
  admin_user_id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  old_data: Record<string, unknown> | null;
  new_data: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}
