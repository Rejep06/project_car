import { apiRequest } from "./client";
import type { Pagination, UserNotification } from "./types";

export function listNotifications(page = 1, pageSize = 20) {
  return apiRequest<Pagination<UserNotification>>(
    `/notifications?page=${page}&page_size=${pageSize}`,
  );
}

export function getUnreadNotificationCount() {
  return apiRequest<{ unread_count: number }>("/notifications/unread-count");
}

export function markNotificationRead(id: string) {
  return apiRequest<UserNotification>(`/notifications/${id}/read`, {
    method: "POST",
  });
}

export function markAllNotificationsRead() {
  return apiRequest<{ message: string }>("/notifications/read-all", {
    method: "POST",
  });
}
