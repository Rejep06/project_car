import { CalendarDays, Clock3, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { getSystemConfig } from "../../api/system";
import type { PublicSystemConfig, Wallet, Withdrawal } from "../../api/types";
import {
  cancelWithdrawal,
  createWithdrawal,
  getWallet,
  listWithdrawals,
} from "../../api/wallet";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate, formatDateOnly } from "../../utils/date";
import { addMoney, percentageFee } from "../../utils/money";

export function WithdrawalsPage() {
  const [items, setItems] = useState<Withdrawal[]>([]);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [config, setConfig] = useState<PublicSystemConfig | null>(null);
  const [address, setAddress] = useState("");
  const [amount, setAmount] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const estimate = useMemo(() => {
    try {
      const fee = percentageFee(amount || "0", config?.withdrawal_fee_percent ?? 0);
      return { fee, total: addMoney(amount || "0", fee) };
    } catch {
      return { fee: "0.000000", total: "0.000000" };
    }
  }, [amount, config]);

  function load() {
    setLoading(true);
    Promise.all([listWithdrawals(page, 10), getWallet(), getSystemConfig()])
      .then(([withdrawals, currentWallet, systemConfig]) => {
        setItems(withdrawals.items);
        setTotal(withdrawals.total);
        setWallet(currentWallet);
        setConfig(systemConfig);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [page]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!config?.withdrawal_is_open) {
      showToast("Заявки на вывод принимаются по средам", "error");
      return;
    }
    setSubmitting(true);
    try {
      await createWithdrawal(address, amount);
      showToast("Заявка на вывод создана", "success");
      setAddress("");
      setAmount("");
      load();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось создать заявку",
        "error",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function cancel(id: string) {
    try {
      await cancelWithdrawal(id);
      showToast("Заявка отменена, средства возвращены", "success");
      load();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось отменить заявку",
        "error",
      );
    }
  }

  const nextDate = config?.next_withdrawal_open_at
    ? formatDateOnly(
        config.next_withdrawal_open_at,
        config.withdrawal_timezone || "Asia/Almaty",
      )
    : "ближайшую среду";

  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">USDT · Ethereum (ERC-20)</p>
          <h1>Вывод средств</h1>
        </div>
      </div>

      <div className={`withdrawal-window-banner ${config?.withdrawal_is_open ? "open" : "closed"}`}>
        <CalendarDays />
        <div>
          <strong>
            {config?.withdrawal_is_open
              ? "Сегодня можно подать заявку на вывод"
              : "Вывод доступен каждую среду"}
          </strong>
          <p>
            Приём заявок идёт по времени Алматы (UTC+5). Обработка занимает от {config?.withdrawal_processing_min_hours ?? 1} часа до {config?.withdrawal_processing_max_days ?? 3} дней.
            {!config?.withdrawal_is_open && ` Ближайшая дата: ${nextDate}.`}
          </p>
        </div>
      </div>

      <div className="two-column align-start">
        <Card>
          <h2>Новая заявка</h2>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Адрес Ethereum
              <input
                required
                placeholder="0x…"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                disabled={!config?.withdrawal_is_open}
              />
            </label>
            <label>
              Сумма к получению
              <input
                required
                inputMode="decimal"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={config?.min_withdrawal_amount ?? "20.000000"}
                disabled={!config?.withdrawal_is_open}
              />
              <span className="field-hint">
                Минимум {config?.min_withdrawal_amount ?? "—"} USDT
              </span>
            </label>
            <dl className="compact-dl">
              <div>
                <dt>К получению</dt>
                <dd><MoneyValue value={amount || "0.000000"} /></dd>
              </div>
              <div>
                <dt>Комиссия ({config?.withdrawal_fee_percent ?? "—"}%)</dt>
                <dd><MoneyValue value={estimate.fee} /></dd>
              </div>
              <div>
                <dt>С баланса спишется</dt>
                <dd><MoneyValue value={estimate.total} /></dd>
              </div>
              <div>
                <dt>Доступно</dt>
                <dd><MoneyValue value={wallet?.available_balance ?? "0.000000"} /></dd>
              </div>
            </dl>
            <p className="field-hint">
              Комиссия — {config?.withdrawal_fee_percent ?? "—"}% от суммы к получению.
              Она добавляется к общей сумме списания.
            </p>
            <Button
              type="submit"
              loading={submitting}
              disabled={!config?.withdrawal_is_open}
            >
              {config?.withdrawal_is_open
                ? "Создать заявку"
                : "Доступно в среду"}
            </Button>
          </form>
        </Card>

        <Card className="withdrawal-terms-card">
          <h2>Условия вывода</h2>
          <div className="withdrawal-term">
            <CalendarDays />
            <div>
              <strong>Каждую среду</strong>
              <p>Заявку можно создать в течение всей среды по времени Алматы.</p>
            </div>
          </div>
          <div className="withdrawal-term">
            <Clock3 />
            <div>
              <strong>От 1 часа до 3 дней</strong>
              <p>Это обычный срок обработки после подачи заявки.</p>
            </div>
          </div>
          <div className="withdrawal-term">
            <ShieldCheck />
            <div>
              <strong>Проверяйте реквизиты</strong>
              <p>Убедитесь, что указали адрес Ethereum (ERC-20) без ошибок.</p>
            </div>
          </div>
        </Card>
      </div>

      <h2>История заявок</h2>
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="notice danger">{error}</div>
      ) : items.length ? (
        <>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Адрес</th>
                  <th>Сумма</th>
                  <th>Комиссия</th>
                  <th>Статус</th>
                  <th>TxID</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td className="break-all">{item.destination_address}</td>
                    <td><MoneyValue value={item.amount} /></td>
                    <td><MoneyValue value={item.fee} /></td>
                    <td><StatusBadge status={item.status} /></td>
                    <td className="break-all">{item.txid ?? "—"}</td>
                    <td>
                      {item.status === "pending_review" && (
                        <Button variant="ghost" onClick={() => void cancel(item.id)}>
                          Отменить
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={10} total={total} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          title="Выводов пока нет"
          text="Заявки на вывод можно создавать каждую среду."
        />
      )}
    </div>
  );
}
