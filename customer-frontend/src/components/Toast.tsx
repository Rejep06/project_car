import { useEffect, useRef, useState } from "react";

export type ToastTone = "success" | "error" | "info";

interface ToastItem {
  id: number;
  message: string;
  tone: ToastTone;
}

const TOAST_EVENT = "automotive:toast";

/**
 * Показывает уведомление без дополнительного React Context.
 * Context API в проекте остаётся только в модуле авторизации.
 */
export function showToast(message: string, tone: ToastTone = "info") {
  window.dispatchEvent(
    new CustomEvent(TOAST_EVENT, {
      detail: { message, tone },
    }),
  );
}

/** Единственная область, которая отображает уведомления приложения. */
export function ToastRegion() {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);
  const timers = useRef<number[]>([]);

  useEffect(() => {
    const activeTimers = timers.current;

    function handleToast(event: Event) {
      const detail = (
        event as CustomEvent<{ message: string; tone: ToastTone }>
      ).detail;
      const id = nextId.current++;
      setItems((current) => [...current, { id, ...detail }]);
      const timer = window.setTimeout(() => {
        setItems((current) => current.filter((item) => item.id !== id));
      }, 3500);
      activeTimers.push(timer);
    }

    window.addEventListener(TOAST_EVENT, handleToast);
    return () => {
      window.removeEventListener(TOAST_EVENT, handleToast);
      activeTimers.forEach((timer) => window.clearTimeout(timer));
    };
  }, []);

  return (
    <div className="toast-region" aria-live="polite" aria-atomic="false">
      {items.map((item) => (
        <div key={item.id} className={`toast toast-${item.tone}`} role="status">
          {item.message}
        </div>
      ))}
    </div>
  );
}
