import { useEffect, useState } from "react";
import type { WalletTransaction } from "../../api/types";
import { listTransactions } from "../../api/wallet";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../utils/date";
export function TransactionsPage() {
  const [items, setItems] = useState<WalletTransaction[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listTransactions(page, 20)
      .then((d) => {
        setItems(d.items);
        setTotal(d.total);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">История баланса</p>
          <h1>Операции кошелька</h1>
        </div>
      </div>
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
                  <th>Операция</th>
                  <th>Описание</th>
                  <th>Доступно Δ</th>
                  <th>Заблокировано Δ</th>
                  <th>Баланс после</th>
                  <th>Дата</th>
                </tr>
              </thead>
              <tbody>
                {items.map((tx) => (
                  <tr key={tx.id}>
                    <td>
                      <StatusBadge status={tx.operation_type} />
                    </td>
                    <td>{tx.description}</td>
                    <td>
                      <MoneyValue value={tx.available_delta} signed />
                    </td>
                    <td>
                      <MoneyValue value={tx.locked_delta} signed />
                    </td>
                    <td>
                      <MoneyValue value={tx.available_after} />
                    </td>
                    <td>{formatDate(tx.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            pageSize={20}
            total={total}
            onChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          title="История пуста"
          text="Все изменения баланса будут отображаться здесь."
        />
      )}
    </div>
  );
}
