import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import type { DepositWallet } from "../api/types";
import { DepositStatusPanel } from "../components/DepositStatusPanel";
import { ToastRegion } from "../components/Toast";
import { DepositDetailsPage } from "../pages/account/DepositDetailsPage";
import { DepositsPage } from "../pages/account/DepositsPage";
import { SupportDetailsPage } from "../pages/account/SupportDetailsPage";
import { SupportPage } from "../pages/account/SupportPage";
import { WithdrawalsPage } from "../pages/account/WithdrawalsPage";
import { formatDate } from "../utils/date";
import {
  errorJson,
  invoice,
  json,
  systemConfig,
  ticket,
  wallet,
  withdrawal,
} from "./fixtures";

function wrap(element: React.ReactElement, route = "/") {
  return render(
    <MemoryRouter
      initialEntries={[route]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AuthProvider>
        <>
          {element}
          <ToastRegion />
        </>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("пополнения, поддержка и выводы", () => {
  it("9. создаётся заявка пополнения", async () => {
    const wallets: DepositWallet[] = [
      { id: invoice().deposit_wallet_id!, title: "Основной кошелёк", address: `0x${"a".repeat(40)}`, asset: "USDT", network: "ETHEREUM", network_display_name: "Ethereum (ERC-20)", sort_order: 0, is_active: true },
      { id: "99999999-9999-4999-8999-999999999999", title: "Резервный кошелёк", address: `0x${"b".repeat(40)}`, asset: "USDT", network: "ETHEREUM", network_display_name: "Ethereum (ERC-20)", sort_order: 1, is_active: true },
    ];
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/wallet/deposit-addresses")) return json(wallets);
        if (path.includes("/wallet/deposits") && init?.method === "POST")
          return json(invoice({ deposit_wallet_id: wallets[1].id, wallet_name: wallets[1].title, address: wallets[1].address }), 201);
        if (path.includes("/wallet/deposits"))
          return json({ items: [], page: 1, page_size: 10, total: 0 });
        if (path.includes("/system/config")) return json(systemConfig);
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    wrap(<DepositsPage />);
    const selectedWallet = await screen.findByRole("radio", { name: /Резервный кошелёк/ });
    await userEvent.click(selectedWallet);
    expect(selectedWallet).toBeChecked();
    await userEvent.type(
      screen.getByLabelText(/Сумма пополнения/),
      "100.000000",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Получить реквизиты" }),
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/wallet/deposits"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ amount: "100.000000", deposit_wallet_id: wallets[1].id }),
        }),
      ),
    );
    expect(
      await screen.findByText("Заявка на пополнение создана"),
    ).toBeInTheDocument();
  });

  it("10. показывается точная сумма", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => json(invoice())),
    );
    wrap(
      <Routes>
        <Route path="/account/deposits/:id" element={<DepositDetailsPage />} />
      </Routes>,
      `/account/deposits/${invoice().id}`,
    );
    expect(await screen.findAllByText("100.347000")).not.toHaveLength(0);
    expect(screen.getByText("Ethereum (ERC-20)")).toBeInTheDocument();
  });

  it("11. показывается основной срок 30 минут", () => {
    render(
      <DepositStatusPanel
        invoice={invoice()}
        now={new Date("2026-07-18T10:10:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Заявка ожидает оплату" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Переведите точную сумму до/)).toHaveTextContent(formatDate(invoice().expires_at));
    expect(screen.queryByRole("heading", { name: "Основной срок заявки завершён" })).not.toBeInTheDocument();
  });

  it("12. после 30 минут показывается период ожидания", () => {
    render(
      <DepositStatusPanel
        invoice={invoice({ status: "expired" })}
        now={new Date("2026-07-18T13:00:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Основной срок заявки завершён" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Если перевод уже выполнен, дождитесь обновления статуса/)).toHaveTextContent(formatDate(invoice().amount_reserved_until));
    expect(screen.queryByRole("heading", { name: "Срок действия реквизитов завершён" })).not.toBeInTheDocument();
  });

  it("13. после 24 часов предлагается обращение", () => {
    render(
      <DepositStatusPanel
        invoice={invoice({ status: "expired" })}
        now={new Date("2026-07-19T10:01:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", {
        name: "Срок действия реквизитов завершён",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Не отправляйте перевод по этой заявке/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Создайте новую заявку или обратитесь в поддержку/)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Заявка ожидает оплату" })).not.toBeInTheDocument();
  });

  it("14. позднее зачисление показывает полученную сумму после истечения срока реквизитов", () => {
    render(
      <DepositStatusPanel
        invoice={invoice({
          status: "credited",
          received_amount: "99.500000",
          credited_after_expiration: true,
        })}
        now={new Date("2026-07-20T10:00:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Платёж успешно зачислен" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Получено:/)).toHaveTextContent("99.500000 USDT");
    expect(screen.queryByText("100.347000")).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Срок действия реквизитов завершён" })).not.toBeInTheDocument();
  });

  it("15. создаётся обращение с TxID", async () => {
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/support/tickets") && init?.method === "POST")
          return json(ticket, 201);
        if (path.includes("/support/tickets"))
          return json({ items: [], page: 1, page_size: 10, total: 0 });
        if (path.includes("/system/config")) return json(systemConfig);
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    wrap(
      <SupportPage />,
      `/account/support?invoiceId=${invoice().id}&expected=100.347000`,
    );
    await userEvent.type(await screen.findByLabelText("TxID"), "a".repeat(64));
    await userEvent.type(
      screen.getByLabelText(/Фактически отправленная сумма/),
      "100.000000",
    );
    await userEvent.type(
      screen.getByLabelText("Описание"),
      "Отправил другую сумму",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Создать обращение" }),
    );
    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([url, init]) =>
          String(url).endsWith("/support/tickets") &&
          (init as RequestInit)?.method === "POST",
      );
      expect(call).toBeTruthy();
      expect(String((call?.[1] as RequestInit).body)).toContain("100.000000");
    });
  });

  it("16. создаётся вывод", async () => {
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/wallet/withdrawals") && init?.method === "POST")
          return json(withdrawal, 201);
        if (path.includes("/wallet/withdrawals"))
          return json({ items: [], page: 1, page_size: 10, total: 0 });
        if (path.endsWith("/wallet")) return json(wallet("100.000000"));
        if (path.includes("/system/config")) return json(systemConfig);
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    wrap(<WithdrawalsPage />);
    await userEvent.type(
      await screen.findByLabelText("Адрес Ethereum"),
      `0x${"b".repeat(40)}`,
    );
    await userEvent.type(
      screen.getByLabelText(/Сумма к получению/),
      "50.000000",
    );
    expect(screen.getByText("Комиссия (10%)")).toBeInTheDocument();
    expect(screen.getByText("5.000000")).toBeInTheDocument();
    expect(screen.getByText("55.000000")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Создать заявку" }),
    );
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          ([url, init]) =>
            String(url).endsWith("/wallet/withdrawals") &&
            (init as RequestInit)?.method === "POST",
        ),
      ).toBe(true),
    );
  });

  it("17. отображается статус вывода", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.includes("/wallet/withdrawals"))
          return json({
            items: [withdrawal],
            page: 1,
            page_size: 10,
            total: 1,
          });
        if (path.endsWith("/wallet")) return json(wallet("100.000000"));
        if (path.includes("/system/config")) return json(systemConfig);
        throw new Error(`unexpected ${path}`);
      }),
    );
    wrap(<WithdrawalsPage />);
    expect(await screen.findByText("Ожидает проверки")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Отменить" }),
    ).toBeInTheDocument();
  });

  it("18. пользователь не открывает чужое обращение через интерфейс", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        errorJson("support_ticket_not_found", "Обращение не найдено", 404),
      ),
    );
    wrap(
      <Routes>
        <Route path="/account/support/:id" element={<SupportDetailsPage />} />
      </Routes>,
      "/account/support/foreign-id",
    );
    expect(await screen.findByText("Обращение не найдено")).toBeInTheDocument();
    expect(screen.queryByText("user@example.com")).not.toBeInTheDocument();
  });
});
