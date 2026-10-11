import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { tokenStore } from "../auth/tokenStore";
import { AccountLayout } from "../components/AccountLayout";
import { useUnreadCount } from "../hooks/useUnreadCount";
import { NotificationsPage } from "../pages/account/NotificationsPage";
import { SupportDetailsPage } from "../pages/account/SupportDetailsPage";
import { SupportPage } from "../pages/account/SupportPage";
import type { SupportTicket, UserNotification } from "../api/types";
import { SUPPORT_READ_EVENT } from "../utils/unreadEvents";
import { errorJson, json, systemConfig, ticket, user } from "./fixtures";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function account(path: string) {
  tokenStore.setTokens("access", "refresh");
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route path="/account" element={<AccountLayout />}>
            <Route index element={<div>Обзор кабинета</div>} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="support" element={<SupportPage />} />
            <Route path="support/:id" element={<SupportDetailsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function notification(id: string): UserNotification {
  return { id, title: `Уведомление ${id}`, message: "Важное сообщение", notification_type: "system", action_url: null, is_read: false, read_at: null, created_at: "2026-10-11T10:00:00Z" };
}

describe("непрочитанные сообщения", () => {
  it("подсвечивает оба раздела и сразу обновляет счётчик после одного и всех уведомлений", async () => {
    let notifications = [notification("first"), notification("second")];
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith("/support/unread-count")) return json({ unread_count: 4 });
      if (path.endsWith("/notifications/unread-count")) return json({ unread_count: notifications.filter((item) => !item.is_read).length });
      if (path.endsWith("/notifications/first/read") && init?.method === "POST") {
        notifications = notifications.map((item) => item.id === "first" ? { ...item, is_read: true } : item);
        return json(notifications[0]);
      }
      if (path.endsWith("/notifications/read-all") && init?.method === "POST") {
        notifications = notifications.map((item) => ({ ...item, is_read: true }));
        return json({ message: "ok" });
      }
      if (path.endsWith("/notifications")) return json({ items: notifications, page: 1, page_size: 100, total: notifications.length });
      throw new Error(`unexpected ${path}`);
    }));
    account("/account/notifications");
    const badge = await screen.findByLabelText("Непрочитанных уведомлений: 2");
    const navLink = badge.closest("a")!;
    expect(navLink).toHaveClass("active", "has-unread");
    expect(screen.getByLabelText("Непрочитанных сообщений поддержки: 4").closest("a")).toHaveClass("has-unread");
    const firstCard = (await screen.findByRole("heading", { name: "Уведомление first" })).closest(".notification-card")!;
    await userEvent.click(within(firstCard as HTMLElement).getByRole("button", { name: "Отметить прочитанным" }));
    expect(await screen.findByLabelText("Непрочитанных уведомлений: 1")).toBeInTheDocument();
    await waitFor(() => expect(firstCard).not.toHaveClass("unread"));
    await userEvent.click(screen.getByRole("button", { name: "Прочитать все" }));
    await waitFor(() => expect(screen.queryByLabelText(/Непрочитанных уведомлений:/)).not.toBeInTheDocument());
    expect(navLink).not.toHaveClass("has-unread");
    expect(screen.getByLabelText("Непрочитанных сообщений поддержки: 4")).toBeInTheDocument();
  });

  it("ошибка чтения не сбрасывает уведомление и счётчик", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith("/support/unread-count")) return json({ unread_count: 0 });
      if (path.endsWith("/notifications/unread-count")) return json({ unread_count: 1 });
      if (init?.method === "POST") return errorJson("unavailable", "Временно недоступно", 503);
      return json({ items: [notification("first")], page: 1, page_size: 100, total: 1 });
    }));
    account("/account/notifications");
    await screen.findByLabelText("Непрочитанных уведомлений: 1");
    await userEvent.click(await screen.findByRole("button", { name: "Отметить прочитанным" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Временно недоступно");
    expect(screen.getByLabelText("Непрочитанных уведомлений: 1")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Уведомление first" }).closest(".notification-card")).toHaveClass("unread");
  });

  it("счётчик обновляется каждые 30 секунд и при возвращении во вкладку, но не в фоне", async () => {
    vi.useFakeTimers();
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    const fetchCount = vi.fn().mockResolvedValue({ unread_count: 2 });
    const { result, unmount } = renderHook(() => useUnreadCount("user", "/account", fetchCount, SUPPORT_READ_EVENT));
    await act(async () => {});
    expect(result.current).toBe(2);
    fetchCount.mockResolvedValue({ unread_count: 3 });
    await act(async () => { vi.advanceTimersByTime(30_000); });
    expect(result.current).toBe(3);
    expect(fetchCount).toHaveBeenCalledTimes(2);
    visibility.mockReturnValue("hidden");
    await act(async () => { vi.advanceTimersByTime(60_000); window.dispatchEvent(new Event("focus")); });
    expect(fetchCount).toHaveBeenCalledTimes(2);
    visibility.mockReturnValue("visible");
    fetchCount.mockResolvedValue({ unread_count: 7 });
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(result.current).toBe(7);
    await act(async () => { window.dispatchEvent(new Event("focus")); });
    expect(fetchCount).toHaveBeenCalledTimes(4);
    unmount();
    await act(async () => { vi.advanceTimersByTime(30_000); window.dispatchEvent(new Event("focus")); });
    expect(fetchCount).toHaveBeenCalledTimes(4);
  });

  it("запоздалый запрос не возвращает старый счётчик после чтения или смены пользователя", async () => {
    const pending: Array<(value: { unread_count: number }) => void> = [];
    const fetchCount = vi.fn(() => new Promise<{ unread_count: number }>((resolve) => pending.push(resolve)));
    const { result, rerender } = renderHook(({ owner }: { owner: string | undefined }) => useUnreadCount(owner, "/account", fetchCount, SUPPORT_READ_EVENT), { initialProps: { owner: "first" as string | undefined } });
    act(() => { window.dispatchEvent(new Event(SUPPORT_READ_EVENT)); });
    await act(async () => { pending[1]({ unread_count: 0 }); });
    await act(async () => { pending[0]({ unread_count: 10 }); });
    expect(result.current).toBe(0);
    rerender({ owner: "second" });
    await act(async () => { pending[2]({ unread_count: 4 }); });
    expect(result.current).toBe(4);
    act(() => { window.dispatchEvent(new Event(SUPPORT_READ_EVENT)); });
    rerender({ owner: undefined });
    expect(result.current).toBe(0);
    await act(async () => { pending[3]({ unread_count: 12 }); });
    expect(result.current).toBe(0);
    rerender({ owner: "first" });
    expect(result.current).toBe(0);
  });

  it("список обращений подсвечивает входящие и показывает справа число, не отмечая их прочитанными", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith("/support/unread-count")) return json({ unread_count: 2 });
      if (path.endsWith("/notifications/unread-count")) return json({ unread_count: 0 });
      if (path.endsWith("/system/config")) return json(systemConfig);
      return json({ items: [{ ...ticket, unread_count: 2 }], page: 1, page_size: 10, total: 1 });
    });
    vi.stubGlobal("fetch", fetchMock);
    account("/account/support");
    const badge = await screen.findByLabelText("Непрочитанных сообщений: 2");
    expect(badge.closest("tr")).toHaveClass("support-unread-row");
    expect(within(badge.parentElement!).getByRole("link", { name: "Открыть" })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/read"))).toBe(false);
  });

  it("читает только увиденные загруженные входящие: скрытая вкладка и остальные сообщения остаются непрочитанными", async () => {
    let data: SupportTicket = { ...ticket, unread_count: 2, messages: [
      { ...ticket.messages[0], read_at: null },
      { ...ticket.messages[0], id: "reply-visible", author_user_id: "admin", message: "Ответ поддержки", read_at: null },
      { ...ticket.messages[0], id: "reply-below", author_user_id: "admin", message: "Другой ответ ниже", read_at: null },
      { ...ticket.messages[0], id: "already-read", author_user_id: "admin", message: "Старый ответ" },
    ] };
    let unreadCount = 3; // Includes a reply which has not been loaded into this thread.
    const readIds: string[][] = [];
    let intersect: IntersectionObserverCallback = () => {};
    const observed: Element[] = [];
    vi.stubGlobal("IntersectionObserver", class {
      constructor(callback: IntersectionObserverCallback) { intersect = callback; }
      observe(element: Element) { observed.push(element); }
      disconnect() {}
    });
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith("/support/unread-count")) return json({ unread_count: unreadCount });
      if (path.endsWith("/notifications/unread-count")) return json({ unread_count: 0 });
      if (path.endsWith(`/support/tickets/${ticket.id}/read`)) {
        const ids = JSON.parse(String(init?.body)).message_ids as string[];
        readIds.push(ids);
        unreadCount -= ids.length;
        data = { ...data, messages: data.messages.map((item) => ids.includes(item.id) ? { ...item, read_at: "2026-10-11T10:05:00Z" } : item) };
        return json({ unread_count: unreadCount });
      }
      if (path.endsWith(`/support/tickets/${ticket.id}`)) return json(data);
      throw new Error(`unexpected ${path}`);
    }));
    account(`/account/support/${ticket.id}`);
    await screen.findByText("Ответ поддержки");
    await screen.findByLabelText("Непрочитанных сообщений поддержки: 3");
    expect(observed.map((element) => element.getAttribute("data-support-message-id"))).toEqual(["reply-visible", "reply-below"]);
    expect(readIds).toEqual([]);
    visibility.mockReturnValue("hidden");
    await act(async () => { intersect([{ target: observed[0], isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver); });
    expect(readIds).toEqual([]);
    visibility.mockReturnValue("visible");
    fireEvent(document, new Event("visibilitychange"));
    await waitFor(() => expect(readIds).toEqual([["reply-visible"]]));
    expect(await screen.findByLabelText("Непрочитанных сообщений поддержки: 2")).toBeInTheDocument();
    expect(data.messages.find((item) => item.id === "reply-below")?.read_at).toBeNull();
    expect(data.messages[0].read_at).toBeNull();
  });

  it("ошибка загрузки обращения не отправляет подтверждение прочтения", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith("/unread-count")) return json({ unread_count: 1 });
      return errorJson("support_ticket_not_found", "Обращение не найдено", 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    account("/account/support/foreign-id");
    expect(await screen.findByText("Обращение не найдено")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/read"))).toBe(false);
  });

  it("позднее завершение отправки в предыдущем обращении не заменяет открытую переписку", async () => {
    let finishSend!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input)).pathname;
      if (init?.method === "POST") return new Promise<Response>((resolve) => { finishSend = resolve; });
      if (path.endsWith("/second")) return json({ ...ticket, id: "second", subject: "Второе обращение" });
      return json({ ...ticket, id: "first", subject: "Первое обращение" });
    }));
    render(<MemoryRouter initialEntries={["/account/support/first"]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Link to="/account/support/second">Перейти ко второму</Link>
      <Routes><Route path="/account/support/:id" element={<SupportDetailsPage />} /></Routes>
    </MemoryRouter>);
    await userEvent.type(await screen.findByLabelText("Сообщение"), "Новый вопрос");
    await userEvent.click(screen.getByRole("button", { name: "Отправить" }));
    await userEvent.click(screen.getByRole("link", { name: "Перейти ко второму" }));
    await screen.findByRole("heading", { name: "Второе обращение" });
    await act(async () => { finishSend(json({ ...ticket.messages[0], id: "new" })); });
    expect(screen.getByRole("heading", { name: "Второе обращение" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Первое обращение" })).not.toBeInTheDocument();
  });
});
