export const SUPPORT_READ_EVENT = "automotive:admin-support-read";

export function notifyUnreadChanged(event: string) {
  window.dispatchEvent(new Event(event));
}
