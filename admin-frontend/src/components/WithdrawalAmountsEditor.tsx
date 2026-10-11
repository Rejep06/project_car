import { useEffect, useRef, useState, type FormEvent } from "react";
import { ApiClientError } from "../api/client";
import {
  getWithdrawalFeeConfig,
  updateWithdrawalAmounts,
} from "../api/withdrawals";
import type { AdminWithdrawal } from "../api/types";
import { formatMoney, fromAtomic, toAtomic } from "../utils/money";
import { Button } from "./Button";
import { FormField } from "./FormField";
import { Modal } from "./Modal";
import "../styles/withdrawals.css";

const MAX_ATOMIC = 9_223_372_036_854_775_807n;

export function WithdrawalAmountsEditor({
  item,
  onUpdated,
  onClose,
}: {
  item: AdminWithdrawal;
  onUpdated: (updated: AdminWithdrawal) => void;
  onClose: () => void;
}) {
  const [amount, setAmount] = useState(item.amount);
  const [fee, setFee] = useState(item.fee);
  const [comment, setComment] = useState("");
  const [feePercent, setFeePercent] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [stale, setStale] = useState(false);
  const requestRef = useRef<{ signature: string; key: string } | null>(null);

  useEffect(() => {
    let active = true;
    getWithdrawalFeeConfig()
      .then((config) => {
        if (
          active &&
          Number.isInteger(config.withdrawal_fee_percent) &&
          config.withdrawal_fee_percent >= 0 &&
          config.withdrawal_fee_percent <= 100
        ) {
          setFeePercent(config.withdrawal_fee_percent);
        }
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  let preview: { amount: bigint; fee: bigint; total: bigint; difference: bigint } | null = null;
  try {
    const amountAtomic = toAtomic(amount);
    const feeAtomic = toAtomic(fee);
    const total = amountAtomic + feeAtomic;
    if (amountAtomic > 0n && feeAtomic >= 0n && total <= MAX_ATOMIC) {
      const current = toAtomic(item.status === "completed" ? item.final_total : item.held_total);
      preview = { amount: amountAtomic, fee: feeAtomic, total, difference: total - current };
    }
  } catch {
    // Незавершённый ввод суммы не отправляется на сервер.
  }

  function calculateFee() {
    if (feePercent === null) return;
    try {
      const value = toAtomic(amount);
      if (value <= 0n) throw new Error("Введите сумму больше нуля");
      setFee(fromAtomic((value * BigInt(feePercent) + 50n) / 100n));
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Проверьте сумму");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || stale) return;
    if (!preview) {
      setError("Введите положительную сумму и неотрицательную комиссию, не более шести знаков после точки.");
      return;
    }
    if (comment.trim().length < 3) {
      setError("Укажите причину изменения: не менее трёх символов.");
      return;
    }
    const data = {
      amount: fromAtomic(preview.amount),
      fee: fromAtomic(preview.fee),
      comment: comment.trim(),
      expected_updated_at: item.updated_at,
    };
    const signature = JSON.stringify(data);
    if (requestRef.current?.signature !== signature) {
      requestRef.current = { signature, key: crypto.randomUUID() };
    }
    setBusy(true);
    setError("");
    try {
      const updated = await updateWithdrawalAmounts(item.id, data, requestRef.current.key);
      onUpdated(updated);
    } catch (cause) {
      if (cause instanceof ApiClientError && cause.code === "withdrawal_changed") setStale(true);
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить изменение");
    } finally {
      setBusy(false);
    }
  }

  const hasBeenSent = item.status === "sent" || item.status === "completed";

  return (
    <Modal open title="Изменить сумму и комиссию" onClose={() => { if (!busy) onClose(); }}>
      <p><strong>{item.user_email}</strong></p>
      {hasBeenSent && (
        <p className="muted">
          Исправление обновит учёт вывода и баланс пользователя. Уже отправленный
          перевод по TxID в блокчейне останется прежним.
        </p>
      )}
      <form onSubmit={submit}>
        <fieldset disabled={busy || stale} className="withdrawal-edit-fields">
          <FormField label="Новая сумма получателю, USDT">
            <input inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} required />
          </FormField>
          <FormField label="Новая комиссия, USDT">
            <input inputMode="decimal" value={fee} onChange={(event) => setFee(event.target.value)} required />
          </FormField>
          {feePercent !== null && (
            <Button type="button" variant="secondary" onClick={calculateFee}>
              Рассчитать {feePercent}% от новой суммы
            </Button>
          )}
          <FormField label="Причина изменения">
            <textarea rows={3} value={comment} onChange={(event) => setComment(event.target.value)} minLength={3} maxLength={1000} required />
          </FormField>
        </fieldset>
        {preview && (
          <div className="withdrawal-edit-preview" aria-live="polite">
            <div className="table-scroll">
              <table className="withdrawal-edit-table" aria-label="Суммы до и после изменения, USDT">
                <thead><tr><th>USDT</th><th>Сейчас</th><th>После изменения</th></tr></thead>
                <tbody>
                  <tr><th scope="row">Получателю</th><td>{formatMoney(item.amount)}</td><td>{formatMoney(fromAtomic(preview.amount))}</td></tr>
                  <tr><th scope="row">Комиссия</th><td>{formatMoney(item.fee)}</td><td>{formatMoney(fromAtomic(preview.fee))}</td></tr>
                  <tr><th scope="row">Всего</th><td>{formatMoney(item.final_total)}</td><td><strong>{formatMoney(fromAtomic(preview.total))}</strong></td></tr>
                </tbody>
              </table>
            </div>
            {item.status !== "completed" && toAtomic(item.held_total) !== toAtomic(item.final_total) && (
              <p>Сейчас заблокировано {formatMoney(item.held_total)} USDT. При сохранении удержание составит {formatMoney(fromAtomic(preview.total))} USDT.</p>
            )}
            <p>
              {preview.difference > 0n
                ? `С доступного баланса будет дополнительно ${item.status === "completed" ? "списано" : "заблокировано"} ${formatMoney(fromAtomic(preview.difference))} USDT.`
                : preview.difference < 0n
                  ? `На доступный баланс вернётся ${formatMoney(fromAtomic(-preview.difference))} USDT.`
                  : "Общая сумма списания не изменится."}
            </p>
          </div>
        )}
        {error && <p className="form-error" role="alert">{error}</p>}
        {stale && <p>Закройте окно, обновите страницу и проверьте актуальные данные заявки.</p>}
        <div className="form-actions">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>Отмена</Button>
          <Button type="submit" loading={busy} disabled={stale || !preview}>Сохранить изменения</Button>
        </div>
      </form>
    </Modal>
  );
}
