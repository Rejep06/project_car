import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listUsers } from "../api/users";
import type { AdminUser } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/date";
import { formatMoney } from "../utils/money";
export function UsersPage() {
  const [items, setItems] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listUsers(page, 20)
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
        title="Пользователи"
        description="Баланс уже включён backend в административный список — дополнительных запросов на каждую строку нет."
      />
      {error && <p className="form-error">{error}</p>}
      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState title="Пользователей нет" description="Список пока пуст." />
      ) : (
        <>
          <DataTable label="Пользователи">
            <thead>
              <tr>
                <th>Email</th>
                <th>Роль</th>
                <th>Состояние</th>
                <th>Доступно</th>
                <th>Заблокировано</th>
                <th>Регистрация</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((u) => (
                <tr key={u.id}>
                  <td>
                    <strong>{u.email}</strong>
                    <small className="mono">{u.id}</small>
                  </td>
                  <td>
                    <StatusBadge value={u.role} />
                  </td>
                  <td>
                    <StatusBadge value={u.is_frozen ? "inactive" : "active"} />
                  </td>
                  <td>
                    {formatMoney(u.available_balance)} {u.asset}
                  </td>
                  <td>
                    {formatMoney(u.locked_balance)} {u.asset}
                  </td>
                  <td>{formatDateTime(u.created_at)}</td>
                  <td>
                    <Link to={`/users/${u.id}`}>Открыть</Link>
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
