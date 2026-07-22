import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listDeposits } from "../api/deposits";
import type { UnmatchedDeposit } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";
export function DepositsPage() {
  const [items, setItems] = useState<UnmatchedDeposit[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listDeposits(page, 20)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  const filtered = useMemo(
    () =>
      items.filter(
        (x) =>
          (!query || x.txid.toLowerCase().includes(query.toLowerCase())) &&
          (!status || x.status === status) &&
          (!reason || x.reason === reason),
      ),
    [items, query, status, reason],
  );
  return (
    <>
      <PageHeader
        title="Нераспознанные пополнения"
        description="Поиск и фильтры применяются к текущей странице: backend пока не принимает эти query-параметры."
      />
      <div className="filter-bar">
        <label>
          Поиск по TxID
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Введите часть TxID"
          />
        </label>
        <label>
          Статус
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Все</option>
            {["unresolved", "assigned", "ignored"].map((x) => (
              <option key={x} value={x}>
                {label(x)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Причина
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="">Все</option>
            {[
              "wrong_amount",
              "expired_invoice",
              "invoice_not_found",
              "duplicate_candidate",
              "unknown",
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
          title="Записей не найдено"
          description="Измените фильтры или перейдите на другую страницу."
        />
      ) : (
        <>
          <DataTable label="Нераспознанные пополнения">
            <thead>
              <tr>
                <th>TxID</th>
                <th>Binance ID</th>
                <th>Сумма</th>
                <th>Сеть</th>
                <th>Причина</th>
                <th>Статус</th>
                <th>Время</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((x) => (
                <tr key={x.id}>
                  <td className="mono truncate" title={x.txid}>
                    {x.txid}
                  </td>
                  <td className="mono truncate" title={x.binance_deposit_id}>
                    {x.binance_deposit_id}
                  </td>
                  <td>{formatMoney(x.amount)} USDT</td>
                  <td>{x.network}</td>
                  <td>{label(x.reason)}</td>
                  <td>
                    <StatusBadge value={x.status} />
                  </td>
                  <td>{formatDateTime(x.deposit_time)}</td>
                  <td>
                    <Link to={`/deposits/${x.id}`}>Открыть</Link>
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
