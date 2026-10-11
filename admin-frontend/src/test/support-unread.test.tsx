import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { tokenStore } from "../auth/tokenStore";
import { AdminLayout } from "../components/AdminLayout";
import { SupportDetailsPage } from "../pages/SupportDetailsPage";
import { SupportPage } from "../pages/SupportPage";
import type { AdminTicket } from "../api/types";
import { admin, page, ticket } from "./fixtures";
import { json, renderRoute } from "./helpers";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

function adminSupport(path: string) {
  tokenStore.setTokens("access", "refresh");
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          <Route element={<AdminLayout />}>
            <Route path="/support" element={<SupportPage />} />
            <Route path="/support/:id" element={<SupportDetailsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("непрочитанные сообщения в панели поддержки", () => {
  it("выделяет обращение и раздел поддержки со счётчиками справа", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(admin);
      if (path.endsWith("/admin/support/unread-count")) return json({ unread_count: 5 });
      return json(page([{ ...ticket, unread_count: 2 }]));
    });
    adminSupport("/support");
    expect((await screen.findByLabelText("Непрочитанных сообщений поддержки: 5")).closest("a")).toHaveClass("active", "has-unread");
    expect((await screen.findByLabelText("Непрочитанных сообщений: 2")).closest("tr")).toHaveClass("support-unread-row");
    expect(fetchMock.mock.calls.some(([url, options]) => String(url).endsWith("/read") && options?.method === "POST")).toBe(false);
  });

  it("при открытии читает входящие пользователя, исключает ответы администраторов и сразу снимает подсветку", async () => {
    vi.stubGlobal("IntersectionObserver", undefined);
    let data: AdminTicket = { ...ticket, unread_count: 1, messages: [
      { ...ticket.messages[0], read_at: null },
      { ...ticket.messages[0], id: "own-reply", author_user_id: admin.id, author_email: admin.email, message: "Ответ администратора", read_at: null },
      { ...ticket.messages[0], id: "other-admin", author_user_id: "another-admin", message: "Ответ коллеги", read_at: null },
      { ...ticket.messages[0], id: "old-user-message", message: "Уже прочитано" },
    ] };
    const readIds: string[][] = [];
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, options) => {
      const path = new URL(String(input)).pathname;
      if (path.endsWith("/users/me")) return json(admin);
      if (path.endsWith("/admin/support/unread-count")) return json({ unread_count: data.unread_count });
      if (path.endsWith(`/admin/support/tickets/${ticket.id}/read`)) {
        const ids = JSON.parse(String(options?.body)).message_ids as string[];
        readIds.push(ids);
        data = { ...data, unread_count: 0, messages: data.messages.map((item) => ids.includes(item.id) ? { ...item, read_at: "2026-10-11T10:05:00Z" } : item) };
        return json({ unread_count: 0 });
      }
      return json(data);
    });
    adminSupport(`/support/${ticket.id}`);
    await screen.findByText("Ответ администратора", { selector: "p" });
    await waitFor(() => expect(readIds).toEqual([[ticket.messages[0].id]]));
    await waitFor(() => expect(screen.queryByLabelText(/Непрочитанных сообщений поддержки:/)).not.toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Поддержка" })).not.toHaveClass("has-unread");
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/admin/support/unread-count"))).toBe(true);
    expect(data.messages[1].read_at).toBeNull();
    expect(data.messages[2].read_at).toBeNull();
  });

  it("обновляет открытую переписку по таймеру и сохраняет выбранный администратором статус", async () => {
    vi.useFakeTimers();
    let calls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      calls += 1;
      return json(calls > 1 ? { ...ticket, messages: [...ticket.messages, { ...ticket.messages[0], id: "new", message: "Пришло ещё сообщение" }] } : ticket);
    });
    renderRoute(<SupportDetailsPage />, `/support/${ticket.id}`, "/support/:id");
    await act(async () => {});
    const select = screen.getByLabelText("Новый статус");
    fireEvent.change(select, { target: { value: "waiting_user" } });
    await act(async () => { vi.advanceTimersByTime(30_000); });
    expect(select).toHaveValue("waiting_user");
    expect(screen.getByText("Пришло ещё сообщение")).toBeInTheDocument();
    expect(calls).toBe(2);
  });

  it("в скрытой вкладке ответ остаётся непрочитанным до возвращения", async () => {
    vi.stubGlobal("IntersectionObserver", undefined);
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
    let wasRead = false;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, options) => {
      if (String(input).endsWith("/read") && options?.method === "POST") {
        wasRead = true;
        return json({ unread_count: 0 });
      }
      return json({ ...ticket, unread_count: wasRead ? 0 : 1, messages: [{ ...ticket.messages[0], read_at: wasRead ? "2026-10-11T10:05:00Z" : null }] });
    });
    renderRoute(<SupportDetailsPage />, `/support/${ticket.id}`, "/support/:id");
    await screen.findByRole("heading", { name: ticket.subject });
    expect(wasRead).toBe(false);
    visibility.mockReturnValue("visible");
    fireEvent(document, new Event("visibilitychange"));
    await waitFor(() => expect(wasRead).toBe(true));
    expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/read"))).toHaveLength(1);
  });
});
