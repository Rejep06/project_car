import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getSubscription } from "../../api/subscriptions";
import type { UserSubscription } from "../../api/types";
import { Card } from "../../components/Card";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../utils/date";
import { multiplyMoney } from "../../utils/money";
import { planTierLabels } from "../../utils/programs";
import { frequencyLabels } from "../../utils/rewards";
export function SubscriptionDetailsPage() {
  const { id = "" } = useParams();
  const [item, setItem] = useState<UserSubscription | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getSubscription(id)
      .then(setItem)
      .catch((e: Error) => setError(e.message));
  }, [id]);
  if (error) return <div className="notice danger">{error}</div>;
  if (!item) return <LoadingSpinner />;
  const total = multiplyMoney(item.reward_amount, item.reward_payouts.length);
  return (
    <div className="account-page">
      <Link to="/account/subscriptions">← Мои программы</Link>
      <div className="page-title">
        <div>
          <p className={`program-tier program-tier-${item.plan_tier}`}>
            {planTierLabels[item.plan_tier]}
          </p>
          <h1>{item.plan_title}</h1>
        </div>
        <StatusBadge status={item.status} />
      </div>
      <div className="dashboard-grid">
        <Card className="metric-card">
          <span>Цена</span>
          <strong>
            <MoneyValue value={item.price} />
          </strong>
        </Card>
        <Card className="metric-card">
          <span>Одно начисление</span>
          <strong>
            <MoneyValue value={item.reward_amount} />
          </strong>
          <span>{frequencyLabels[item.reward_frequency]}</span>
        </Card>
        <Card className="metric-card">
          <span>Выплат в графике</span>
          <strong>{item.reward_payouts.length}</strong>
        </Card>
        <Card className="metric-card">
          <span>Предусмотренная сумма</span>
          <strong>
            <MoneyValue value={total} />
          </strong>
        </Card>
      </div>
      <Card>
        <h2>График начислений</h2>
        {item.reward_payouts.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                  <th>Зачислено</th>
                </tr>
              </thead>
              <tbody>
                {item.reward_payouts.map((p) => (
                  <tr key={p.id}>
                    <td>{formatDate(p.due_at)}</td>
                    <td>
                      <MoneyValue value={p.amount} />
                    </td>
                    <td>
                      <StatusBadge status={p.status} />
                    </td>
                    <td>{formatDate(p.paid_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">
            Для этой программы выплаты не предусмотрены или график пуст.
          </p>
        )}
      </Card>
    </div>
  );
}
