import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { AuthProvider } from "../auth/AuthContext";
import { PlanFormPage } from "../pages/PlanFormPage";
import { PlansPage } from "../pages/PlansPage";
import { admin, ordinaryUser, page, plan } from "./fixtures";
import { json, renderRoute } from "./helpers";

function app() {
  return render(
    <MemoryRouter
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("авторизация администратора", () => {
  it("1. неавторизованный пользователь перенаправляется на login", async () => {
    app();
    expect(
      await screen.findByRole("heading", { name: "Вход администратора" }),
    ).toBeInTheDocument();
  });

  it("2. обычный пользователь не допускается", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/auth/login"))
        return json({
          access_token: "a",
          refresh_token: "r",
          token_type: "bearer",
          expires_in: 900,
        });
      if (url.endsWith("/users/me")) return json(ordinaryUser);
      return json({ error: { code: "not_found", message: "Нет" } }, 404);
    });
    app();
    await userEvent.type(
      await screen.findByLabelText("Email"),
      ordinaryUser.email,
    );
    await userEvent.type(screen.getByLabelText("Пароль"), "User123!");
    await userEvent.click(screen.getByRole("button", { name: "Войти" }));
    expect(
      await screen.findByText(
        "Эта учётная запись не имеет роли администратора",
      ),
    ).toBeInTheDocument();
  });

  it("3. администратор входит", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) =>
      String(input).endsWith("/auth/login")
        ? json({
            access_token: "a",
            refresh_token: "r",
            token_type: "bearer",
            expires_in: 900,
          })
        : String(input).endsWith("/users/me")
          ? json(admin)
          : json(page([])),
    );
    app();
    await userEvent.type(await screen.findByLabelText("Email"), admin.email);
    await userEvent.type(screen.getByLabelText("Пароль"), "Admin123!");
    await userEvent.click(screen.getByRole("button", { name: "Войти" }));
    expect(
      await screen.findByRole("heading", { name: "Обзор" }),
    ).toBeInTheDocument();
  });
});

describe("управление подписками", () => {
  it("4. загружается список подписок", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(await json(page([plan])));
    renderRoute(<PlansPage />);
    expect(await screen.findByText("Программа Standard")).toBeInTheDocument();
    expect(screen.getByText("100.000000 USDT")).toBeInTheDocument();
  });

  it("5. создаётся подписка", async () => {
    let sent: unknown;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (_input, init) => {
      sent = init?.body ? JSON.parse(String(init.body)) : null;
      return json(plan);
    });
    renderRoute(<PlanFormPage />);
    await userEvent.type(
      screen.getByLabelText("Название"),
      "Программа Standard",
    );
    await userEvent.type(screen.getByLabelText(/^Slug/), "standard");
    await userEvent.type(
      screen.getByLabelText("Стоимость, USDT"),
      "100.000000",
    );
    await userEvent.type(
      screen.getByLabelText("Сумма одного начисления, USDT"),
      "5.000000",
    );
    fireEvent.submit(
      screen.getByRole("button", { name: "Сохранить" }).closest("form")!,
    );
    await waitFor(() =>
      expect(sent).toMatchObject({
        title: "Программа Standard",
        price: "100.000000",
        reward_amount: "5.000000",
      }),
    );
  });

  it("6. работает изменение подписки", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    fetchMock.mockImplementation((_input, init) =>
      init?.method === "PATCH"
        ? json({ ...plan, title: "Обновлённая программа" })
        : json(plan),
    );
    renderRoute(<PlanFormPage />, `/plans/${plan.id}`, "/plans/:id");
    const title = await screen.findByLabelText("Название");
    await userEvent.clear(title);
    await userEvent.type(title, "Обновлённая программа");
    await userEvent.click(screen.getByRole("button", { name: "Сохранить" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/admin/plans/${plan.id}`),
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });
});
