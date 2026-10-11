export const SUPPORT_READ_EVENT = "automotive:support-read";
export const NOTIFICATIONS_READ_EVENT = "automotive:notifications-read";

export function notifyUnreadChanged(event: string) {
  window.dispatchEvent(new Event(event));
}
