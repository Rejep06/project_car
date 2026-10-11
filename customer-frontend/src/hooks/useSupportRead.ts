import { useEffect, type RefObject } from "react";
import { markTicketRead } from "../api/support";
import type { SupportTicket } from "../api/types";

export function useSupportRead(ticket: SupportTicket | null, thread: RefObject<HTMLDivElement>) {
  useEffect(() => {
    if (!ticket || !thread.current) return;
    const unreadIds = new Set(ticket.messages
      .filter((message) => message.author_user_id !== ticket.user_id && message.read_at === null)
      .map((message) => message.id));
    if (!unreadIds.size) return;

    const ticketId = ticket.id;
    const visibleIds = new Set<string>();
    let active = true;
    let pending = false;
    async function markVisibleMessages() {
      if (!active || pending || document.visibilityState === "hidden") return;
      const messageIds = [...visibleIds].filter((id) => unreadIds.has(id));
      if (!messageIds.length) return;
      pending = true;
      let succeeded = false;
      try {
        // Acknowledge only loaded incoming messages shown in the visible thread.
        // Replies arriving after the load retain their unread state.
        await markTicketRead(ticketId, messageIds);
        messageIds.forEach((id) => unreadIds.delete(id));
        succeeded = true;
      } catch {
        // Retry on the next refresh/focus without losing the unread state.
      } finally {
        pending = false;
      }
      if (succeeded) void markVisibleMessages();
    }

    let observer: IntersectionObserver | undefined;
    if (typeof IntersectionObserver !== "undefined") {
      observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          const id = entry.target.getAttribute("data-support-message-id");
          if (!id || !unreadIds.has(id)) continue;
          if (entry.isIntersecting) visibleIds.add(id);
          else visibleIds.delete(id);
        }
        void markVisibleMessages();
      });
      thread.current.querySelectorAll("[data-support-message-id]").forEach((element) => {
        if (unreadIds.has(element.getAttribute("data-support-message-id")!)) observer!.observe(element);
      });
    } else {
      // Fallback for older browsers: opening a visible conversation reads its loaded replies.
      unreadIds.forEach((id) => visibleIds.add(id));
      void markVisibleMessages();
    }
    window.addEventListener("focus", markVisibleMessages);
    document.addEventListener("visibilitychange", markVisibleMessages);
    return () => {
      active = false;
      observer?.disconnect();
      window.removeEventListener("focus", markVisibleMessages);
      document.removeEventListener("visibilitychange", markVisibleMessages);
    };
  }, [ticket, thread]);
}
