import { Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { activatePlan, deactivatePlan, listPlans } from "../api/plans";
import type { Plan } from "../api/types";
import { Button } from "../components/Button";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";
export function PlansPage() {
  const [data, setData] = useState<{ items: Plan[]; total: number }>({
    items: [],
    total: 0,
  });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const load = useCallback(() => {
    setLoading(true);
    listPlans(page, 20)
      .then((r) => setData(r))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  useEffect(load, [load]);
  async function toggle(plan: Plan) {
    setMessage("");
    try {
      await (plan.is_active ? deactivatePlan(plan.id) : activatePlan(plan.id));
      setMessage(
        plan.is_active ? "Программа деактивирована" : "Программа активирована",
      );
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  return (
    <>
      <PageHeader
        title="Программы"
        description="Название, описание, фотография и условия клиентских программ."
        actions={
          <Link className="button button-primary" to="/plans/new">
            <Plus />
            Создать программу
          </Link>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      {loading ? (
        <LoadingSpinner />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="Программ пока нет"
          description="Создайте первую клиентскую программу."
        />
      ) : (
        <>
          <DataTable label="Клиентские программы">
            <thead>
              <tr>
                <th>Название</th>
                <th>Стоимость</th>
                <th>Срок</th>
                <th>Вознаграждение</th>
                <th>Статус</th>
                <th>Изменено</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.title}</strong>
                    <small>{label(p.tier)}</small>
                  </td>
                  <td>
                    {formatMoney(p.price)} {p.asset}
                  </td>
                  <td>
                    {p.access_duration_value} {label(p.access_duration_unit)}
                  </td>
                  <td>
                    {formatMoney(p.reward_amount)} / {label(p.reward_frequency)}
                  </td>
                  <td>
                    <StatusBadge value={p.is_active ? "active" : "inactive"} />
                  </td>
                  <td>{formatDateTime(p.updated_at)}</td>
                  <td className="row-actions">
                    <Link to={`/plans/${p.id}`}>Открыть</Link>
                    <Button variant="ghost" onClick={() => toggle(p)}>
                      {p.is_active ? "Деактивировать" : "Активировать"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <Pagination
            page={page}
            pageSize={20}
            total={data.total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}
