import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AuthProvider } from "../auth/AuthContext";
import { RegisterPage } from "../pages/RegisterPage";
import { json } from "./fixtures";

function renderRegistration() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/check-email" element={<div>Проверьте email</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("юридические согласия регистрации", () => {
  it("показывает три обязательных чекбокса и отправляет пять версий документов", async () => {
    const fetchMock = vi.fn<typeof fetch>(
      async (input) => {
        if (String(input).endsWith("/auth/register")) {
          return json(
            {
              email: "client@example.com",
              verification_required: true,
              message: "Письмо отправлено",
              debug_verification_token: null,
            },
            201,
          );
        }
        throw new Error(`unexpected ${String(input)}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    const person = userEvent.setup();
    renderRegistration();

    expect(screen.getAllByRole("checkbox")).toHaveLength(3);

    await person.type(screen.getByLabelText("Email"), "client@example.com");
    await person.type(screen.getByLabelText(/^Пароль/), "Strong123!");
    await person.type(screen.getByLabelText("Повторите пароль"), "Strong123!");
    for (const checkbox of screen.getAllByRole("checkbox")) {
      await person.click(checkbox);
    }
    await person.click(screen.getByRole("button", { name: "Создать аккаунт" }));

    expect(await screen.findByText("Проверьте email")).toBeInTheDocument();
    const registerCall = fetchMock.mock.calls.find(([url]) =>
      String(url).endsWith("/auth/register"),
    );
    expect(registerCall).toBeDefined();
    const payload = JSON.parse(String(registerCall?.[1]?.body));
    expect(payload).toMatchObject({
      email: "client@example.com",
      accept_terms: true,
      accept_privacy_policy: true,
      accept_personal_data_processing: true,
      accept_program_rules: true,
      confirm_age_18: true,
    });
  });
});
