import { Gift, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import type { WalletTransaction } from "../../api/types";
import { listTransactions } from "../../api/wallet";
import { Card } from "../../components/Card";
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
      .then((data) =>
        setItems(
          data.items.filter((item) =>
            ["reward_credit", "referral_reward_bonus"].includes(item.operation_type),
          ),
        ),
      )
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">История начислений</p>
          <h1>Вознаграждения</h1>
        </div>
      </div>

      <Card className="rewards-intro-card">
        <Gift />
        <div>
          <h2>Все полученные вознаграждения в одном месте</h2>
          <p>
            Здесь отображаются начисления по активированным программам и
            дополнительные премиальные реферальные бонусы.
          </p>
        </div>
      </Card>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="notice danger">{error}</div>
      ) : items.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Тип</th>
                <th>Описание</th>
                <th>Сумма</th>
                <th>Баланс после</th>
                <th>Дата</th>
              </tr>
            </thead>
            <tbody>
              {items.map((tx) => (
                <tr key={tx.id}>
                  <td>
                    <span className={`reward-type ${tx.operation_type === "referral_reward_bonus" ? "premium" : "program"}`}>
                      {tx.operation_type === "referral_reward_bonus" ? (
                        <><Sparkles size={15} /> Премиум-бонус</>
                      ) : (
                        <><Gift size={15} /> По программе</>
                      )}
                    </span>
                  </td>
                  <td>{tx.description}</td>
                  <td><MoneyValue value={tx.available_delta} signed /></td>
                  <td><MoneyValue value={tx.available_after} /></td>
                  <td>{formatDate(tx.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="Вознаграждений пока нет"
          text="После первого начисления оно появится в этом разделе."
        />
      )}
    </div>
  );
}
