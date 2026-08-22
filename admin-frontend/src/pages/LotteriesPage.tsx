import { Plus, Ticket, Trophy } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listLotteries } from "../api/lotteries";
import type { LotterySummary } from "../api/types";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime } from "../utils/date";
import { formatMoney } from "../utils/money";

const pageSize = 20;

export function LotteriesPage() {
  const [items, setItems] = useState<LotterySummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    listLotteries(page, pageSize)
      .then((result) => {
        setItems(result.items);
        setTotal(result.total);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [page]);

  useEffect(load, [load]);

  return (
    <>
      <PageHeader
        title="Лотереи"
        description="Продажа билетов, призы, выбор и подтверждение победителей."
        actions={
          <Link className="button button-primary" to="/lotteries/new">
            <Plus size={18} /> Создать лотерею
          </Link>
        }
      />
      {error && <p className="form-error">{error}</p>}
      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState
          title="Лотерей пока нет"
          description="Создайте лотерею, добавьте призы и опубликуйте продажи билетов."
        />
      ) : (
        <>
          <DataTable label="Лотереи">
            <thead>
              <tr>
                <th>Название</th>
                <th>Билет</th>
                <th>Продажи до</th>
                <th>Результаты</th>
                <th>Билеты</th>
                <th>Победители</th>
                <th>Статус</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.title}</strong>
                    <small className="mono">{item.id}</small>
                  </td>
                  <td>{formatMoney(item.ticket_price)} {item.asset}</td>
                  <td>{formatDateTime(item.sales_end_at)}</td>
                  <td>{formatDateTime(item.draw_at)}</td>
                  <td><span className="table-icon-value"><Ticket size={16} /> {item.tickets_sold}</span></td>
                  <td><span className="table-icon-value"><Trophy size={16} /> {item.confirmed_winners_count}</span></td>
                  <td><StatusBadge value={item.status} /></td>
                  <td><Link to={`/lotteries/${item.id}`}>Управлять</Link></td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}
