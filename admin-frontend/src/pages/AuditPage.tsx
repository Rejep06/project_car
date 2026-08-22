import { useEffect, useState } from "react";
import { listAudit } from "../api/audit";
import type { AuditLog } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { formatDateTime } from "../utils/date";
export function AuditPage() {
  const [items, setItems] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listAudit(page, 20)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  return (
    <>
      <PageHeader
        title="Журнал действий"
        description="История действий администраторов и изменений важных данных."
      />
      {error && <p className="form-error">{error}</p>}
      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState
          title="Журнал пуст"
          description="Административных событий пока нет."
        />
      ) : (
        <>
          <DataTable label="Журнал аудита">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Администратор</th>
                <th>Действие</th>
                <th>Объект</th>
                <th>IP</th>
                <th>Данные</th>
              </tr>
            </thead>
            <tbody>
              {items.map((x) => (
                <tr key={x.id}>
                  <td>{formatDateTime(x.created_at)}</td>
                  <td className="mono truncate">{x.admin_user_id}</td>
                  <td>{x.action}</td>
                  <td>
                    {x.entity_type}
                    <small className="mono">{x.entity_id ?? "—"}</small>
                  </td>
                  <td>{x.ip_address ?? "—"}</td>
                  <td>
                    <details>
                      <summary>Показать изменения</summary>
                      <div className="audit-json">
                        <h4>До</h4>
                        <pre>{JSON.stringify(x.old_data, null, 2)}</pre>
                        <h4>После</h4>
                        <pre>{JSON.stringify(x.new_data, null, 2)}</pre>
                      </div>
                    </details>
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
