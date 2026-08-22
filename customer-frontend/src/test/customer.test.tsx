import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { AuthProvider } from "../auth/AuthContext";
import { PlanCard } from "../components/PlanCard";
import { ToastRegion } from "../components/Toast";
import { json, lottery, plan, user, wallet } from "./fixtures";

function renderApp(route: string) {
  return render(
    <MemoryRouter
      initialEntries={[route]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AuthProvider>
        <>
          <App />
          <ToastRegion />
        </>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function dashboardResponses(path: string): Response | null {
  if (path.endsWith("/wallet")) return json(wallet());
  if (path.includes("/subscriptions"))
    return json({ items: [], page: 1, page_size: 5, total: 0 });
  if (path.includes("/wallet/transactions"))
    return json({ items: [], page: 1, page_size: 5, total: 0 });
  if (path.includes("/wallet/withdrawals"))
    return json({ items: [], page: 1, page_size: 5, total: 0 });
  if (path.includes("/support/tickets"))
    return json({ items: [], page: 1, page_size: 5, total: 0 });
  return null;
}

describe("клиентский сайт", () => {
  it("1. главная страница загружается", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.includes("/plans"))
          return json({ items: [plan], page: 1, page_size: 6, total: 1 });
        if (path.includes("/posts"))
          return json({ items: [], page: 1, page_size: 3, total: 0 });
        if (path.includes("/lotteries"))
          return json({ items: [lottery], page: 1, page_size: 12, total: 1 });
        throw new Error(`unexpected ${path}`);
      }),
    );
    renderApp("/");
    expect(
      await screen.findByRole("heading", {
        name: /автомобильная компания с клиентскими программами/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/с 2023 года/i)).toBeInTheDocument();
    expect(
      screen
        .getByRole("img", { name: /автомобиль в современном шоуруме/i })
        .getAttribute("src"),
    ).toContain("hero-car-photo.jpg");
    expect(
      await screen.findByRole("heading", { name: "Розыгрыш автомобиля" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Открыть лотерею" })).toHaveAttribute(
      "href",
      `/lotteries/${lottery.id}`,
    );
  });

  it("2. отображается список программ", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        if (String(input).includes("/plans"))
          return json({ items: [plan], page: 1, page_size: 100, total: 1 });
        throw new Error("unexpected");
      }),
    );
    renderApp("/plans");
    expect(await screen.findByText("Программа Standard")).toBeInTheDocument();
    expect(screen.getByText("Стандарт")).toBeInTheDocument();
  });

  it("3. карточка программы показывает условия", () => {
    render(
      <MemoryRouter
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <PlanCard plan={plan} />
      </MemoryRouter>,
    );
    expect(screen.getByText("100.000000")).toBeInTheDocument();
    expect(screen.getByText(/каждую неделю/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /подробнее/i })).toHaveAttribute(
      "href",
      `/plans/${plan.id}`,
    );
    expect(
      screen
        .getByRole("img", {
          name: /автомобиль для программы «программа standard»/i,
        })
        .getAttribute("src"),
    ).toContain("program-car-photo.jpg");
  });

  it("4. работает регистрация с автоматическим входом", async () => {
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = String(input);
        if (path.endsWith("/auth/register")) return json(user, 201);
        if (path.endsWith("/auth/login"))
          return json({
            access_token: "access",
            refresh_token: "refresh",
            token_type: "bearer",
            expires_in: 900,
          });
        if (path.endsWith("/users/me")) return json(user);
        const dashboard = dashboardResponses(path);
        if (dashboard) return dashboard;
        throw new Error(`unexpected ${path} ${init?.method}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    renderApp("/register");
    await userEvent.type(screen.getByLabelText("Email"), "user@example.com");
    await userEvent.type(screen.getByLabelText(/^Пароль/), "Password1!");
    await userEvent.type(
      screen.getByLabelText("Повторите пароль"),
      "Password1!",
    );
    await userEvent.click(
      screen.getByRole("button", { name: /создать аккаунт/i }),
    );
    expect(
      await screen.findByRole("heading", { name: "Обзор" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/auth/register"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("5. работает вход", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/auth/login"))
          return json({
            access_token: "access",
            refresh_token: "refresh",
            token_type: "bearer",
            expires_in: 900,
          });
        if (path.endsWith("/users/me")) return json(user);
        const dashboard = dashboardResponses(path);
        if (dashboard) return dashboard;
        throw new Error(`unexpected ${path}`);
      }),
    );
    renderApp("/login");
    await userEvent.type(screen.getByLabelText("Email"), "user@example.com");
    await userEvent.type(screen.getByLabelText(/^Пароль/), "Password1!");
    await userEvent.click(screen.getByRole("button", { name: "Войти" }));
    expect(
      await screen.findByRole("heading", { name: "Обзор" }),
    ).toBeInTheDocument();
  });

  it("6. защищённый маршрут требует авторизацию", async () => {
    vi.stubGlobal("fetch", vi.fn());
    renderApp("/account");
    expect(
      await screen.findByRole("heading", { name: "Вход" }),
    ).toBeInTheDocument();
  });

  async function renderAuthenticatedPlan(available: string) {
    localStorage.setItem("automotive_customer_refresh_token", "refresh");
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (path.endsWith("/auth/refresh"))
        return json({
          access_token: "access",
          refresh_token: "refresh-2",
          token_type: "bearer",
          expires_in: 900,
        });
      if (path.endsWith("/users/me")) return json(user);
      if (path.endsWith(`/plans/${plan.id}`)) return json(plan);
      if (path.endsWith("/wallet")) return json(wallet(available));
      throw new Error(`unexpected ${path}`);
    });
    vi.stubGlobal("fetch", fetchMock);
    renderApp(`/plans/${plan.id}`);
    await screen.findByRole("heading", { name: "Программа Standard" });
    return fetchMock;
  }

  it("7. недостаточный баланс блокирует активацию", async () => {
    const fetchMock = await renderAuthenticatedPlan("50.000000");
    await userEvent.click(
      screen.getByRole("button", { name: "Активировать программу" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Недостаточно средств" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/не хватает/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Пополнить баланс" }),
    ).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(([url]) => String(url).includes("/purchase")),
    ).toBe(false);
  });

  it("8. открывается подтверждение активации при достаточном балансе", async () => {
    await renderAuthenticatedPlan("150.000000");
    await userEvent.click(
      screen.getByRole("button", { name: "Активировать программу" }),
    );
    expect(
      await screen.findByRole("heading", { name: "Подтверждение активации" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/баланс после активации/i)).toBeInTheDocument();
    expect(screen.getByText("50.000000")).toBeInTheDocument();
  });
});
