import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listSubscriptions } from "../../api/subscriptions";
import type { UserSubscription } from "../../api/types";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDateOnly } from "../../utils/date";
import { planTierLabels } from "../../utils/programs";
export function SubscriptionsPage() {
  const [items, setItems] = useState<UserSubscription[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listSubscriptions(page, 12)
      .then((d) => {
        setItems(d.items);
        setTotal(d.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Клиентские программы</p>
          <h1>Мои программы</h1>
        </div>
        <Link className="button button-primary" to="/plans">
          Выбрать программу
        </Link>
      </div>
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="notice danger">{error}</div>
      ) : items.length ? (
        <>
          <div className="subscription-grid">
            {items.map((item) => (
              <Card key={item.id}>
                <div className="card-heading">
                  <div>
                    <p className={`program-tier program-tier-${item.plan_tier}`}>
                      {planTierLabels[item.plan_tier]}
                    </p>
                    <h2>{item.plan_title}</h2>
                  </div>
                  <StatusBadge status={item.status} />
                </div>
                <dl className="compact-dl">
                  <div>
                    <dt>Стоимость</dt>
                    <dd>
                      <MoneyValue value={item.price} />
                    </dd>
                  </div>
                  <div>
                    <dt>Доступ до</dt>
                    <dd>{formatDateOnly(item.access_ends_at)}</dd>
                  </div>
                  <div>
                    <dt>Одно вознаграждение</dt>
                    <dd>
                      <MoneyValue value={item.reward_amount} />
                    </dd>
                  </div>
                </dl>
                <Link
                  className="button button-secondary"
                  to={`/account/subscriptions/${item.id}`}
                >
                  Открыть график
                </Link>
              </Card>
            ))}
          </div>
          <Pagination
            page={page}
            pageSize={12}
            total={total}
            onChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          title="Программ пока нет"
          text="Выберите активную программу в публичном каталоге."
          action={
            <Link className="button button-primary" to="/plans">
              Каталог
            </Link>
          }
        />
      )}
    </div>
  );
}
