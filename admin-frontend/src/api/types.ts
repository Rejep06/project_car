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
  pending_email: string | null;
  email_verified_at: string | null;
  email_verified: boolean;
  role: "user" | "admin";
  is_active: boolean;
  is_frozen: boolean;
  referral_code: string;
  referred_by_user_id: string | null;
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
export type PlanTier = "starter" | "standard" | "premium";
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
export interface PlanInput {
  title: string;
  tier: PlanTier;
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
export interface DepositWallet {
  id: string;
  title: string;
  address: string;
  asset: string;
  network: string;
  network_display_name: string;
  provider: string;
  provider_network: string | null;
  chain_id: number | null;
  token_standard: string | null;
  token_contract_address: string | null;
  token_decimals: number;
  confirmations_required: number;
  monitoring_enabled: boolean;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
export interface DepositWalletInput {
  title: string;
  address: string;
  asset: string;
  network: string;
  network_display_name: string;
  provider: string;
  provider_network: string | null;
  chain_id: number | null;
  token_standard: string | null;
  token_contract_address: string | null;
  token_decimals: number;
  confirmations_required: number;
  monitoring_enabled: boolean;
  sort_order: number;
  is_active: boolean;
}
export interface UnmatchedDeposit {
  id: string;
  blockchain_record_id: string;
  event_id: string;
  txid: string;
  log_index: number;
  block_number: number | null;
  block_hash: string | null;
  from_address: string | null;
  asset: string;
  amount: string;
  address: string;
  network: string;
  provider: string;
  token_contract_address: string | null;
  deposit_status:
    | "pending"
    | "success"
    | "rejected"
    | "credited_locked"
    | "wrong_deposit"
    | "waiting_confirmation"
    | "unknown";
  confirmations: number;
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
  read_at: string | null;
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
  unread_count: number;
  messages: SupportMessage[];
  expected_amount: string | null;
  actual_amount: string | null;
  deposit_event_id: string | null;
  deposit_txid: string | null;
  deposit_address: string | null;
  deposit_network: string | null;
  deposit_status: string | null;
  deposit_detected_at: string | null;
  deposit_raw_data: Record<string, unknown> | null;
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


export type LotteryStatus =
  | "draft"
  | "published"
  | "awaiting_confirmation"
  | "completed"
  | "cancelled";
export type LotteryPrizeType = "balance" | "physical";
export type LotteryTicketStatus = "active" | "refunded";
export type LotteryWinnerStatus = "pending" | "confirmed" | "cancelled";
export type LotteryWinnerSelectionMethod = "random" | "manual";

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

export interface LotteryPrizeInput {
  title: string;
  description: string;
  prize_type: LotteryPrizeType;
  amount: string | null;
  quantity: number;
  sort_order: number;
  image_url: string | null;
  manager_telegram: string | null;
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

export interface LotteryInput {
  title: string;
  description: string;
  cover_image_url: string | null;
  ticket_price: string;
  sales_start_at: string;
  sales_end_at: string;
  draw_at: string;
  max_tickets_total: number | null;
  max_tickets_per_user: number;
  manager_telegram: string | null;
  rules_text: string;
  rules_version: string;
}

export interface LotteryAdminTicket {
  id: string;
  user_id: string;
  user_email: string;
  ticket_code: string;
  status: LotteryTicketStatus;
  purchased_at: string;
  is_winner: boolean;
}

export interface LotteryWinnerAdmin {
  id: string;
  lottery_id: string;
  prize_id: string;
  prize_title: string;
  prize_type: LotteryPrizeType;
  prize_amount: string | null;
  ticket_id: string;
  ticket_code: string;
  user_id: string;
  user_email: string;
  selection_method: LotteryWinnerSelectionMethod;
  status: LotteryWinnerStatus;
  selected_at: string;
  confirmed_at: string | null;
  claim_contact: string | null;
  confirmation_note: string | null;
}

export interface LotteryAdmin extends LotterySummary {
  manager_telegram: string | null;
  rules_text: string;
  rules_version: string;
  prizes: LotteryPrize[];
  winners: LotteryWinnerPublic[];
  created_by_user_id: string;
  published_at: string | null;
  completed_at: string | null;
  pending_winners_count: number;
  admin_winners: LotteryWinnerAdmin[];
}
