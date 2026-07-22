import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AuditPage } from "../pages/AuditPage";
import { DepositDetailsPage } from "../pages/DepositDetailsPage";
import { DepositsPage } from "../pages/DepositsPage";
import { PostsPage } from "../pages/PostsPage";
import { SupportDetailsPage } from "../pages/SupportDetailsPage";
import { SupportPage } from "../pages/SupportPage";
import { WithdrawalDetailsPage } from "../pages/WithdrawalDetailsPage";
import { WithdrawalsPage } from "../pages/WithdrawalsPage";
import { audit, deposit, page, post, ticket, withdrawal } from "./fixtures";
import { json, renderRoute } from "./helpers";

describe("рабочие разделы администратора", () => {
  it("7. отображаются нераспознанные депозиты", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      await json(page([deposit])),
    );
    renderRoute(<DepositsPage />);
    expect(await screen.findByText("100.000000 USDT")).toBeInTheDocument();
    expect(screen.getAllByText("Неправильная сумма").length).toBeGreaterThan(0);
  });

  it("8. открывается депозит", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(deposit));
    renderRoute(
      <DepositDetailsPage />,
      `/deposits/${deposit.id}`,
      "/deposits/:id",
    );
    expect(
      await screen.findByRole("heading", { name: "Данные депозита" }),
    ).toBeInTheDocument();
    expect(screen.getByText(deposit.txid)).toBeInTheDocument();
  });

  it("9. требуется подтверждение ручного зачисления", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(deposit));
    renderRoute(
      <DepositDetailsPage />,
      `/deposits/${deposit.id}`,
      "/deposits/:id",
    );
    await userEvent.type(
      await screen.findByLabelText("UUID пользователя"),
      "00000000-0000-4000-8000-000000000002",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Зачислить фактическую сумму" }),
    );
    expect(
      await screen.findByRole("dialog", {
        name: "Подтвердить ручное зачисление",
      }),
    ).toBeInTheDocument();
  });

  it("10. отображаются выводы", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      await json(page([withdrawal])),
    );
    renderRoute(<WithdrawalsPage />);
    expect(await screen.findByText(withdrawal.user_email)).toBeInTheDocument();
    expect(screen.getByText("50.000000 USDT")).toBeInTheDocument();
  });

  it("11. mark-sent требует TxID", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(withdrawal));
    renderRoute(
      <WithdrawalDetailsPage />,
      `/withdrawals/${withdrawal.id}`,
      "/withdrawals/:id",
    );
    await screen.findByRole("heading", { name: "Отметить отправленным" });
    await userEvent.type(
      screen.getByLabelText("Фактическая комиссия, USDT"),
      "1.000000",
    );
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Отметить отправленным" })
        .closest("form")!,
    );
    expect(
      await screen.findByText("Для отметки отправки требуется TxID"),
    ).toBeInTheDocument();
  });

  it("12. отображаются обращения", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(page([ticket])));
    renderRoute(<SupportPage />);
    expect(
      await screen.findByText("Не найдено пополнение"),
    ).toBeInTheDocument();
    expect(screen.getByText(ticket.user_email)).toBeInTheDocument();
  });

  it("13. администратор отвечает", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock.mockImplementation((_input, init) =>
      init?.method === "POST"
        ? json({
            ...ticket.messages[0],
            id: "new",
            author_email: "admin@example.com",
            message: "Проверяем",
          })
        : json(ticket),
    );
    renderRoute(
      <SupportDetailsPage />,
      `/support/${ticket.id}`,
      "/support/:id",
    );
    await userEvent.type(
      await screen.findByLabelText("Ответ администратора"),
      "Проверяем",
    );
    await userEvent.click(screen.getByRole("button", { name: "Ответить" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/admin/support/tickets/${ticket.id}/messages`),
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("14. отображаются новости", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(page([post])));
    renderRoute(<PostsPage />);
    expect(await screen.findByText("Новость компании")).toBeInTheDocument();
    expect(screen.getByText("Черновик")).toBeInTheDocument();
  });

  it("15. отображается audit log", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(page([audit])));
    renderRoute(<AuditPage />);
    expect(await screen.findByText("plan_updated")).toBeInTheDocument();
    expect(screen.getByText("subscription_plan")).toBeInTheDocument();
  });

  it("16. ошибки API показываются корректно", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      await json(
        { error: { code: "forbidden", message: "Недостаточно прав" } },
        403,
      ),
    );
    renderRoute(<DepositsPage />);
    expect(await screen.findByText("Недостаточно прав")).toBeInTheDocument();
  });
});
