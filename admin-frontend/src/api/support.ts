import { apiDownload, apiRequest } from "./client";
import type { AdminTicket, Pagination, SupportMessage } from "./types";
export const listTickets = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<AdminTicket>>(
    `/admin/support/tickets?page=${page}&page_size=${pageSize}`,
  );
export const getTicket = (id: string) =>
  apiRequest<AdminTicket>(`/admin/support/tickets/${id}`);
export const addMessage = (id: string, message: string, txid?: string) =>
  apiRequest<SupportMessage>(`/admin/support/tickets/${id}/messages`, {
    method: "POST",
    body: JSON.stringify({ message, ...(txid ? { txid } : {}) }),
  });
export const updateStatus = (id: string, status: AdminTicket["status"]) =>
  apiRequest<AdminTicket>(`/admin/support/tickets/${id}/status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
export const resolveDeposit = (id: string, invoiceId?: string) =>
  apiRequest<AdminTicket>(`/admin/support/tickets/${id}/resolve-deposit`, {
    method: "POST",
    body: JSON.stringify(invoiceId ? { invoice_id: invoiceId } : {}),
  });
export const downloadAttachment = (id: string) =>
  apiDownload(`/support/attachments/${id}`);
