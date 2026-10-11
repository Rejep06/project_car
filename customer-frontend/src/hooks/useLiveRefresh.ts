import { useEffect } from "react";

export function useLiveRefresh(refresh: () => void | Promise<unknown>) {
  useEffect(() => {
    function refreshVisible() {
      if (document.visibilityState !== "hidden") {
        void Promise.resolve().then(refresh).catch(() => undefined);
      }
    }
    const interval = window.setInterval(refreshVisible, 30_000);
    window.addEventListener("focus", refreshVisible);
    document.addEventListener("visibilitychange", refreshVisible);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", refreshVisible);
      document.removeEventListener("visibilitychange", refreshVisible);
    };
  }, [refresh]);
}
