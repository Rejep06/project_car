import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listWithdrawals } from "../api/withdrawals";
import type { AdminWithdrawal } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";
export function WithdrawalsPage() {
  const [items, setItems] = useState<AdminWithdrawal[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listWithdrawals(page, 20)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  const filtered = useMemo(
    () => items.filter((x) => !status || x.status === status),
    [items, status],
  );
  return (
    <>
      <PageHeader
        title="Ручные выводы"
        description="Проверьте заявку, выполните перевод и сохраните TxID операции."
      />
      <div className="filter-bar">
        <label>
          Статус
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Все</option>
            {[
              "pending_review",
              "approved",
              "sent",
              "completed",
              "rejected",
              "cancelled",
            ].map((x) => (
              <option key={x} value={x}>
                {label(x)}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && <p className="form-error">{error}</p>}
      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Заявок нет"
          description="На текущей странице нет подходящих выводов."
        />
      ) : (
        <>
          <DataTable label="Заявки на вывод">
            <thead>
              <tr>
                <th>Пользователь</th>
                <th>Сумма</th>
                <th>Комиссия</th>
                <th>Адрес</th>
                <th>Статус</th>
                <th>Создано</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((x) => (
                <tr key={x.id}>
                  <td>
                    {x.user_email}
                    <small className="mono">{x.user_id}</small>
                  </td>
                  <td>
                    {formatMoney(x.amount)} {x.asset}
                  </td>
                  <td>
                    {formatMoney(x.fee)} {x.asset}
                  </td>
                  <td className="mono truncate" title={x.destination_address}>
                    {x.destination_address}
                  </td>
                  <td>
                    <StatusBadge value={x.status} />
                  </td>
                  <td>{formatDateTime(x.created_at)}</td>
                  <td>
                    <Link to={`/withdrawals/${x.id}`}>Открыть</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <Pagination
            page={page}
            pageSize={20}
            total={total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}
