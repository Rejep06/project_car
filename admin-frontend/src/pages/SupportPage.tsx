import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listTickets } from "../api/support";
import type { AdminTicket } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
export function SupportPage() {
  const [items, setItems] = useState<AdminTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listTickets(page, 20)
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
        title="Обращения"
        description="Сообщения, TxID, вложения и ручное разрешение проблемных пополнений."
      />
      <div className="filter-bar">
        <label>
          Статус
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Все</option>
            {["open", "in_review", "waiting_user", "resolved", "closed"].map(
              (x) => (
                <option key={x} value={x}>
                  {label(x)}
                </option>
              ),
            )}
          </select>
        </label>
      </div>
      {error && <p className="form-error">{error}</p>}
      {loading ? (
        <LoadingSpinner />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Обращений нет"
          description="На текущей странице нет подходящих обращений."
        />
      ) : (
        <>
          <DataTable label="Обращения">
            <thead>
              <tr>
                <th>Пользователь</th>
                <th>Тема</th>
                <th>Категория</th>
                <th>TxID</th>
                <th>Статус</th>
                <th>Последнее сообщение</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td>{t.user_email}</td>
                  <td>
                    <strong>{t.subject}</strong>
                    {t.txid_conflict && (
                      <small className="warning-text">
                        Возможный конфликт TxID
                      </small>
                    )}
                  </td>
                  <td>{label(t.category)}</td>
                  <td className="mono truncate">
                    {t.messages.find((m) => m.txid)?.txid ?? "—"}
                  </td>
                  <td>
                    <StatusBadge value={t.status} />
                  </td>
                  <td>
                    {formatDateTime(
                      t.messages.at(-1)?.created_at ?? t.updated_at,
                    )}
                  </td>
                  <td>
                    <Link to={`/support/${t.id}`}>Открыть</Link>
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
