import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { listTickets } from "../api/support";
import type { AdminTicket } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { useLiveRefresh } from "../hooks/useLiveRefresh";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
export function SupportPage() {
  const [items, setItems] = useState<AdminTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const loadVersion = useRef(0);
  const load = useCallback(async (background = false) => {
    const version = ++loadVersion.current;
    if (!background) setLoading(true);
    try {
      const r = await listTickets(page, 20);
      if (version === loadVersion.current) {
        setItems(r.items);
        setTotal(r.total);
        setError("");
      }
    } catch (reason) {
      if (version === loadVersion.current) setError(reason instanceof Error ? reason.message : "Не удалось загрузить обращения");
    } finally {
      if (version === loadVersion.current) setLoading(false);
    }
  }, [page]);
  useEffect(() => {
    void load();
    return () => { loadVersion.current += 1; };
  }, [load]);
  const refresh = useCallback(() => load(true), [load]);
  useLiveRefresh(refresh);
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
                <tr key={t.id} className={t.unread_count > 0 ? "support-unread-row" : undefined}>
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
                    <div className="support-row-actions">
                      <Link to={`/support/${t.id}`}>Открыть</Link>
                      {t.unread_count > 0 && <span className="unread-count" aria-label={`Непрочитанных сообщений: ${t.unread_count}`}>{t.unread_count > 99 ? "99+" : t.unread_count}</span>}
                    </div>
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
