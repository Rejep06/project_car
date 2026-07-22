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
import { formatDate } from "../../utils/date";
import { addMoney } from "../../utils/money";

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
  const totalDebit = useMemo(() => {
    try {
      return addMoney(amount || "0", config?.withdrawal_fee ?? "0");
    } catch {
      return "0.000000";
    }
  }, [amount, config]);
  function load() {
    setLoading(true);
    Promise.all([listWithdrawals(page, 10), getWallet(), getSystemConfig()])
      .then(([w, wal, c]) => {
        setItems(w.items);
        setTotal(w.total);
        setWallet(wal);
        setConfig(c);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(load, [page]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createWithdrawal(address, amount);
      showToast("Заявка на вывод создана", "success");
      setAddress("");
      setAmount("");
      load();
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось создать вывод",
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
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Ручной вывод USDT</p>
          <h1>Заявки на вывод</h1>
        </div>
      </div>
      <div className="two-column align-start">
        <Card>
          <h2>Новая заявка</h2>
          <p>
            Администратор проверяет заявку и вручную отправляет USDT через
            интерфейс Binance.
          </p>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Адрес TRON
              <input
                required
                placeholder="T…"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </label>
            <label>
              Сумма, которую вы получите
              <input
                required
                inputMode="decimal"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder={config?.min_withdrawal_amount ?? "20.000000"}
              />
              <span className="field-hint">
                Минимум {config?.min_withdrawal_amount ?? "—"} USDT
              </span>
            </label>
            <dl className="compact-dl">
              <div>
                <dt>Пользователь получит</dt>
                <dd>
                  <MoneyValue value={amount || "0.000000"} />
                </dd>
              </div>
              <div>
                <dt>Комиссия</dt>
                <dd>
                  <MoneyValue value={config?.withdrawal_fee ?? "0.000000"} />
                </dd>
              </div>
              <div>
                <dt>С баланса спишется</dt>
                <dd>
                  <MoneyValue value={totalDebit} />
                </dd>
              </div>
              <div>
                <dt>Доступно</dt>
                <dd>
                  <MoneyValue value={wallet?.available_balance ?? "0.000000"} />
                </dd>
              </div>
            </dl>
            <Button type="submit" loading={submitting}>
              Создать заявку
            </Button>
          </form>
        </Card>
        <Card>
          <h2>Как проходит вывод</h2>
          <ol className="ordered-steps">
            <li>Сумма и комиссия переходят из available в locked.</li>
            <li>Администратор проверяет адрес и заявку.</li>
            <li>После ручной отправки появляется TxID.</li>
            <li>После завершения locked balance уменьшается.</li>
          </ol>
          <p className="small muted">
            Выводы обрабатываются через внутренний процесс проверки заявок.
          </p>
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
                    <td>
                      <MoneyValue value={item.amount} />
                    </td>
                    <td>
                      <MoneyValue value={item.fee} />
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="break-all">{item.txid ?? "—"}</td>
                    <td>
                      {item.status === "pending_review" && (
                        <Button
                          variant="ghost"
                          onClick={() => void cancel(item.id)}
                        >
                          Отменить
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            pageSize={10}
            total={total}
            onChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          title="Выводов пока нет"
          text="Создайте заявку после пополнения внутреннего баланса."
        />
      )}
    </div>
  );
}
