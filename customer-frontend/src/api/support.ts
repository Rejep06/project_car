import { apiDownload, apiRequest } from "./client";
import { notifyUnreadChanged, SUPPORT_READ_EVENT } from "../utils/unreadEvents";
import type {
  Attachment,
  Pagination,
  SupportMessage,
  SupportTicket,
} from "./types";

export interface TicketInput {
  category: SupportTicket["category"];
  subject: string;
  message: string;
  txid?: string;
  related_deposit_invoice_id?: string;
}

export const createTicket = (data: TicketInput) =>
  apiRequest<SupportTicket>("/support/tickets", {
    method: "POST",
    body: JSON.stringify(data),
  });
export const listTickets = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<SupportTicket>>(
    `/support/tickets?page=${page}&page_size=${pageSize}`,
  );
export const getTicket = (id: string) =>
  apiRequest<SupportTicket>(`/support/tickets/${id}`);
export const getUnreadSupportCount = () =>
  apiRequest<{ unread_count: number }>("/support/unread-count");
export async function markTicketRead(id: string, messageIds: string[]) {
  let result = { unread_count: 0 };
  for (let offset = 0; offset < messageIds.length; offset += 1000) {
    result = await apiRequest<{ unread_count: number }>(`/support/tickets/${id}/read`, {
      method: "POST",
      body: JSON.stringify({ message_ids: messageIds.slice(offset, offset + 1000) }),
    });
    notifyUnreadChanged(SUPPORT_READ_EVENT);
  }
  return result;
}
export const addTicketMessage = (id: string, message: string, txid?: string) =>
  apiRequest<SupportMessage>(`/support/tickets/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ message, ...(txid ? { txid } : {}) }),
  });
export const uploadAttachments = (messageId: string, files: File[]) => {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  return apiRequest<Attachment[]>(
    `/support/messages/${messageId}/attachments`,
    { method: "POST", body: form },
  );
};
export const downloadAttachment = (id: string) =>
  apiDownload(`/support/attachments/${id}`);
