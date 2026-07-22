import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { WalletTransaction } from "../../api/types";
import { listTransactions } from "../../api/wallet";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { formatDate } from "../../utils/date";
export function RewardsPage() {
  const [items, setItems] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    listTransactions(1, 100)
      .then((d) =>
        setItems(
          d.items.filter((item) => item.operation_type === "reward_credit"),
        ),
      )
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Reward payout</p>
          <h1>Полученные вознаграждения по программам</h1>
        </div>
        <Link className="button button-secondary" to="/account/subscriptions">
          Будущие графики
        </Link>
      </div>
      <div className="notice info">
        Здесь отображаются фактически начисленные вознаграждения по вашим
        клиентским программам. Будущий график начислений доступен внутри
        каждой программы.
      </div>
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="notice danger">{error}</div>
      ) : items.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Описание</th>
                <th>Сумма</th>
                <th>Баланс после</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {items.map((tx) => (
                <tr key={tx.id}>
                  <td>{tx.description}</td>
                  <td>
                    <MoneyValue value={tx.available_delta} signed />
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
      ) : (
        <EmptyState
          title="Вознаграждений пока нет"
          text="После обработки reward worker операции появятся здесь."
        />
      )}
    </div>
  );
}
