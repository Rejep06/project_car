import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Link } from "react-router-dom";
import { WithdrawalDetailsPage } from "../pages/WithdrawalDetailsPage";
import type { AdminWithdrawal } from "../api/types";
import { withdrawal } from "./fixtures";
import { json, renderRoute } from "./helpers";

function setup(item: AdminWithdrawal = withdrawal) {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
    if (String(input).endsWith("/system/config")) return json({ withdrawal_fee_percent: 10 });
    if (init?.method === "PATCH") {
      const payload = JSON.parse(init.body as string);
      return json({ ...item, amount: payload.amount, fee: payload.fee, updated_at: "2026-10-11T10:00:00Z" });
    }
    return json(item);
  });
  renderRoute(<WithdrawalDetailsPage />, `/withdrawals/${item.id}`, "/withdrawals/:id");
  return fetchMock;
}

async function openEditor() {
  await userEvent.click(await screen.findByRole("button", { name: "Изменить сумму и комиссию" }));
  return screen.findByRole("dialog", { name: "Изменить сумму и комиссию" });
}

describe("исправление сумм вывода администратором", () => {
  it("предзаполняет фактическую комиссию сохранённой комиссией заявки", async () => {
    setup();
    expect(await screen.findByLabelText("Фактическая комиссия, USDT")).toHaveValue(withdrawal.fee);
  });

  it("считает 10% с округлением и отправляет выбранный вывод с причиной и защитой повторов", async () => {
    const fetchMock = setup();
    const dialog = await openEditor();
    fireEvent.change(within(dialog).getByLabelText("Новая сумма получателю, USDT"), { target: { value: "20.000005" } });
    await userEvent.click(await within(dialog).findByRole("button", { name: "Рассчитать 10% от новой суммы" }));
    expect(within(dialog).getByLabelText("Новая комиссия, USDT")).toHaveValue("2.000001");
    expect(within(dialog).getByText("На доступный баланс вернётся 29.999994 USDT.")).toBeInTheDocument();
    fireEvent.change(within(dialog).getByLabelText("Причина изменения"), { target: { value: "Исправление ошибки суммы" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Сохранить изменения" }));
    await screen.findByText("Сумма и комиссия обновлены, баланс пересчитан");
    const call = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
    expect(call?.[0]).toContain(`/admin/withdrawals/${withdrawal.id}/amounts`);
    const options = call?.[1];
    expect(JSON.parse(options?.body as string)).toEqual({
      amount: "20.000005", fee: "2.000001", comment: "Исправление ошибки суммы", expected_updated_at: withdrawal.updated_at,
    });
    expect(new Headers(options?.headers).get("Idempotency-Key")).toBeTruthy();
  });

  it("показывает перерасчёт завершённого вывода по фактическому списанию", async () => {
    setup({ ...withdrawal, status: "completed", held_total: "55.000000", final_total: "52.000000", txid: `0x${"a".repeat(64)}` });
    const dialog = await openEditor();
    expect(within(dialog).getByText(/Уже отправленный перевод по TxID/)).toBeInTheDocument();
    fireEvent.change(within(dialog).getByLabelText("Новая сумма получателю, USDT"), { target: { value: "40" } });
    fireEvent.change(within(dialog).getByLabelText("Новая комиссия, USDT"), { target: { value: "4" } });
    expect(within(dialog).getByText("На доступный баланс вернётся 8.000000 USDT.")).toBeInTheDocument();
  });

  it("отрицательную комиссию не отправляет", async () => {
    const fetchMock = setup();
    const dialog = await openEditor();
    fireEvent.change(within(dialog).getByLabelText("Новая комиссия, USDT"), { target: { value: "-1" } });
    expect(within(dialog).getByRole("button", { name: "Сохранить изменения" })).toBeDisabled();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "PATCH")).toBe(false);
  });

  it("не предлагает изменение отменённой заявки", async () => {
    setup({ ...withdrawal, status: "cancelled" });
    await screen.findByRole("heading", { name: "Заявка на вывод" });
    expect(screen.queryByRole("button", { name: "Изменить сумму и комиссию" })).not.toBeInTheDocument();
  });

  it("сохраняет один idempotency key при повторе после сетевой ошибки", async () => {
    const fetchMock = setup();
    const dialog = await openEditor();
    let failures = 0;
    fetchMock.mockImplementation((input, init) => {
      if (init?.method === "PATCH" && failures++ === 0) return Promise.reject(new Error("Связь потеряна"));
      if (String(input).endsWith("/system/config")) return json({ withdrawal_fee_percent: 10 });
      return json(withdrawal);
    });
    fireEvent.change(within(dialog).getByLabelText("Причина изменения"), { target: { value: "Уточнение комиссии" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Сохранить изменения" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Связь потеряна");
    await userEvent.click(within(dialog).getByRole("button", { name: "Сохранить изменения" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    const calls = fetchMock.mock.calls.filter(([, init]) => init?.method === "PATCH");
    expect(calls).toHaveLength(2);
    expect(new Headers(calls[0][1]?.headers).get("Idempotency-Key")).toEqual(new Headers(calls[1][1]?.headers).get("Idempotency-Key"));
  });

  it("после stale conflict требует обновить заявку вместо перезаписи чужого изменения", async () => {
    const fetchMock = setup();
    const dialog = await openEditor();
    fetchMock.mockImplementation((_input, init) => init?.method === "PATCH"
      ? json({ error: { code: "withdrawal_changed", message: "Заявка уже изменена" } }, 409)
      : json({ withdrawal_fee_percent: 10 }));
    fireEvent.change(within(dialog).getByLabelText("Причина изменения"), { target: { value: "Исправление комиссии" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Сохранить изменения" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Заявка уже изменена");
    expect(within(dialog).getByRole("button", { name: "Сохранить изменения" })).toBeDisabled();
  });

  it("поздний ответ сохранения предыдущей заявки не подменяет данные новой заявки", async () => {
    const other = { ...withdrawal, id: "40000000-0000-4000-8000-000000000002", user_email: "other@example.com" };
    let finishRequest: ((response: Response) => void) | undefined;
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      if (init?.method === "PATCH") return new Promise<Response>((resolve) => { finishRequest = resolve; });
      if (String(input).endsWith("/system/config")) return json({ withdrawal_fee_percent: 10 });
      return json(String(input).endsWith(other.id) ? other : withdrawal);
    });
    renderRoute(
      <><Link to={`/withdrawals/${other.id}`}>Другая заявка</Link><WithdrawalDetailsPage /></>,
      `/withdrawals/${withdrawal.id}`,
      "/withdrawals/:id",
    );
    const dialog = await openEditor();
    fireEvent.change(within(dialog).getByLabelText("Причина изменения"), { target: { value: "Уточнение суммы" } });
    await userEvent.click(within(dialog).getByRole("button", { name: "Сохранить изменения" }));
    await userEvent.click(screen.getByRole("link", { name: "Другая заявка" }));
    await screen.findByText(other.user_email);
    await act(async () => { finishRequest?.(await json(withdrawal)); });
    expect(screen.getByText(other.user_email)).toBeInTheDocument();
    expect(screen.queryByText(withdrawal.user_email)).not.toBeInTheDocument();
  });
});
