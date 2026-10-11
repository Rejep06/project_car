import { apiRequest } from "./client";
import type { Pagination, UserNotification } from "./types";
import { NOTIFICATIONS_READ_EVENT, notifyUnreadChanged } from "../utils/unreadEvents";

export function listNotifications(page = 1, pageSize = 20) {
  return apiRequest<Pagination<UserNotification>>(
    `/notifications?page=${page}&page_size=${pageSize}`,
  );
}

export function getUnreadNotificationCount() {
  return apiRequest<{ unread_count: number }>("/notifications/unread-count");
}

export async function markNotificationRead(id: string) {
  const result = await apiRequest<UserNotification>(`/notifications/${id}/read`, {
    method: "POST",
  });
  notifyUnreadChanged(NOTIFICATIONS_READ_EVENT);
  return result;
}

export async function markAllNotificationsRead() {
  const result = await apiRequest<{ message: string }>("/notifications/read-all", {
    method: "POST",
  });
  notifyUnreadChanged(NOTIFICATIONS_READ_EVENT);
  return result;
}
