import { useEffect, useState } from "react";

export function useUnreadCount(
  userId: string | undefined,
  pathname: string,
  fetchCount: () => Promise<{ unread_count: number }>,
  changeEvent: string,
) {
  const [snapshot, setSnapshot] = useState({ userId, count: 0 });

  useEffect(() => {
    setSnapshot((current) => current.userId === userId ? current : { userId, count: 0 });
    if (!userId) return;
    let active = true;
    let requestVersion = 0;

    async function refresh() {
      if (!userId || document.visibilityState === "hidden") return;
      const version = ++requestVersion;
      try {
        const result = await fetchCount();
        // A response started before a read action must not restore an old count.
        if (active && version === requestVersion) {
          setSnapshot({ userId, count: Math.max(0, result.unread_count) });
        }
      } catch {
        // Keep the last known count during a temporary network failure.
      }
    }

    void refresh();
    const interval = window.setInterval(() => void refresh(), 30_000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    window.addEventListener(changeEvent, refresh);
    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener(changeEvent, refresh);
    };
  }, [userId, pathname, fetchCount, changeEvent]);

  // Never show another account's cached count, even during the first render.
  return userId && snapshot.userId === userId ? snapshot.count : 0;
}
