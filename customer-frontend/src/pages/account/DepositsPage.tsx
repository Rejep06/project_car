import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getSystemConfig } from "../../api/system";
import type { DepositInvoice, PublicSystemConfig } from "../../api/types";
import { createDeposit, listDeposits } from "../../api/wallet";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";

export function DepositsPage() {
  const [items, setItems] = useState<DepositInvoice[]>([]);
  const [config, setConfig] = useState<PublicSystemConfig | null>(null);
  const [amount, setAmount] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  function load() {
    setLoading(true);
    Promise.all([listDeposits(page, 10), getSystemConfig()])
      .then(([d, c]) => {
        setItems(d.items);
        setTotal(d.total);
        setConfig(c);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(load, [page]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    try {
      const invoice = await createDeposit(amount);
      showToast("Заявка на пополнение создана", "success");
      navigate(`/account/deposits/${invoice.id}`);
    } catch (e) {
      showToast(
        e instanceof Error ? e.message : "Не удалось создать заявку",
        "error",
      );
    } finally {
      setCreating(false);
    }
  }
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">USDT · TRON (TRC20)</p>
          <h1>Пополнение баланса</h1>
        </div>
      </div>
      <div className="two-column align-start">
        <Card>
          <h2>Новая заявка</h2>
          <p>
            Система добавит уникальную трёхзначную дробную часть и зарезервирует
            точную сумму.
          </p>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Желаемая сумма USDT
              <input
                required
                inputMode="decimal"
                placeholder={config?.min_deposit_amount ?? "10.000000"}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
              <span className="field-hint">
                Минимум: {config?.min_deposit_amount ?? "загружается"} USDT
              </span>
            </label>
            <Button type="submit" loading={creating}>
              Создать заявку
            </Button>
          </form>
          <div className="notice warning">
            <strong>Перед переводом</strong>
            <p>
              Отправьте ровно указанную сумму через сеть TRON (TRC20). Проверьте
              поле «Получатель получит» в Binance или Bybit.
            </p>
          </div>
        </Card>
        <Card>
          <h2>Сроки распознавания</h2>
          <dl className="compact-dl">
            <div>
              <dt>Основной срок</dt>
              <dd>{config?.deposit_invoice_ttl_minutes ?? 30} минут</dd>
            </div>
            <div>
              <dt>Резерв точной суммы</dt>
              <dd>{config?.deposit_amount_reservation_hours ?? 24} часа</dd>
            </div>
          </dl>
          <p>
            После завершения основного срока точный платёж всё ещё может быть
            зачислен автоматически до конца резервирования.
          </p>
        </Card>
      </div>
      <h2>Мои заявки</h2>
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
                  <th>Создана</th>
                  <th>Желаемая сумма</th>
                  <th>Точная сумма</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>
                      <MoneyValue value={item.requested_amount} />
                    </td>
                    <td>
                      <MoneyValue value={item.expected_amount} />
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>
                      <Link to={`/account/deposits/${item.id}`}>Открыть</Link>
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
          title="Заявок пока нет"
          text="Создайте первую заявку, чтобы получить точную сумму и адрес."
        />
      )}
    </div>
  );
}
