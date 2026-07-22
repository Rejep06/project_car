import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { DepositStatusPanel } from "../components/DepositStatusPanel";
import { ToastRegion } from "../components/Toast";
import { DepositDetailsPage } from "../pages/account/DepositDetailsPage";
import { DepositsPage } from "../pages/account/DepositsPage";
import { SupportDetailsPage } from "../pages/account/SupportDetailsPage";
import { SupportPage } from "../pages/account/SupportPage";
import { WithdrawalsPage } from "../pages/account/WithdrawalsPage";
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
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.includes("/wallet/deposits") && init?.method === "POST")
          return json(invoice(), 201);
        if (path.includes("/wallet/deposits"))
          return json({ items: [], page: 1, page_size: 10, total: 0 });
        if (path.includes("/system/config")) return json(systemConfig);
        throw new Error(`unexpected ${path}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    wrap(<DepositsPage />);
    await userEvent.type(
      await screen.findByLabelText(/Желаемая сумма USDT/),
      "100.000000",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Создать заявку" }),
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/wallet/deposits"),
        expect.objectContaining({ method: "POST" }),
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
    expect(screen.getByText("TRON (TRC20)")).toBeInTheDocument();
  });

  it("11. показывается основной срок 30 минут", () => {
    render(
      <DepositStatusPanel
        invoice={invoice()}
        now={new Date("2026-07-18T10:10:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Основной срок оплаты" }),
    ).toBeInTheDocument();
  });

  it("12. после 30 минут показывается период ожидания", () => {
    render(
      <DepositStatusPanel
        invoice={invoice({ status: "expired" })}
        now={new Date("2026-07-18T13:00:00Z")}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Ожидаем возможный поздний платёж" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/продолжит проверку до/i)).toBeInTheDocument();
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
        name: "Период автоматического распознавания завершён",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/создайте обращение и укажите TxID/i),
    ).toBeInTheDocument();
  });

  it("14. показывается позднее зачисление", () => {
    render(
      <DepositStatusPanel
        invoice={invoice({
          status: "credited",
          received_amount: "100.347000",
          credited_after_expiration: true,
        })}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Платёж успешно зачислен" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/после основного срока/i)).toBeInTheDocument();
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
      await screen.findByLabelText("Адрес TRON"),
      `T${"B".repeat(33)}`,
    );
    await userEvent.type(
      screen.getByLabelText(/Сумма, которую вы получите/),
      "50.000000",
    );
    expect(screen.getByText("52.000000")).toBeInTheDocument();
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
