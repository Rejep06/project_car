import { CalendarDays, CheckCircle2, Coins } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { getPlan } from "../api/plans";
import { purchaseSubscription } from "../api/subscriptions";
import type { Plan, Wallet } from "../api/types";
import { getWallet } from "../api/wallet";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { MoneyValue } from "../components/MoneyValue";
import { showToast } from "../components/Toast";
import { compareMoney, subtractMoney } from "../utils/money";
import {
  durationLabels,
  estimateRewardCount,
  estimateRewardTotal,
  frequencyLabels,
} from "../utils/rewards";

export function PlanDetailsPage() {
  const { slug = "" } = useParams();
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [purchasing, setPurchasing] = useState(false);
  const idempotencyKey = useRef(crypto.randomUUID());
  useEffect(() => {
    Promise.all([getPlan(slug), user ? getWallet() : Promise.resolve(null)])
      .then(([planData, walletData]) => {
        setPlan(planData);
        setWallet(walletData);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug, user]);
  if (loading)
    return (
      <div className="page-center">
        <LoadingSpinner />
      </div>
    );
  if (error || !plan)
    return (
      <section className="section">
        <div className="container notice danger">
          {error || "Программа не найдена"}
        </div>
      </section>
    );
  const currentPlan = plan;
  const enough = wallet
    ? compareMoney(wallet.available_balance, currentPlan.price) >= 0
    : false;
  const count = estimateRewardCount(currentPlan);
  function openPurchase() {
    if (!user) {
      navigate("/login", { state: { from: location.pathname } });
      return;
    }
    setConfirmOpen(true);
  }
  async function purchase() {
    setPurchasing(true);
    try {
      const subscription = await purchaseSubscription(
        currentPlan.id,
        idempotencyKey.current,
      );
      showToast("Программа успешно активирована", "success");
      navigate(`/account/subscriptions/${subscription.id}`);
    } catch (e) {
      showToast(
        e instanceof Error ? e.message : "Не удалось активировать программу",
        "error",
      );
    } finally {
      setPurchasing(false);
    }
  }
  return (
    <section className="section page-hero">
      <div className="container plan-detail-grid">
        <div className="plan-detail-main">
          <p className="eyebrow">Клиентская программа</p>
          <h1>{plan.title}</h1>
          <p className="lead">{plan.short_description}</p>
          <div className="description-block">
            <h2>Что входит в программу</h2>
            {plan.full_description
              .split("\n")
              .filter(Boolean)
              .map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
          </div>
          <Card className="schedule-card">
            <h2>График вознаграждений</h2>
            <div className="schedule-grid">
              <div>
                <Coins />
                <span>Размер начисления</span>
                <strong>
                  <MoneyValue value={plan.reward_amount} />
                </strong>
              </div>
              <div>
                <CalendarDays />
                <span>Частота</span>
                <strong>{frequencyLabels[plan.reward_frequency]}</strong>
              </div>
              <div>
                <CheckCircle2 />
                <span>Период</span>
                <strong>
                  {plan.reward_duration_value}{" "}
                  {durationLabels[plan.reward_duration_unit]}
                </strong>
              </div>
            </div>
            <p>
              Ориентировочное количество начислений: <strong>{count}</strong>
            </p>
            <p>
              Ориентировочная предусмотренная сумма вознаграждений:{" "}
              <strong>
                <MoneyValue value={estimateRewardTotal(plan)} />
              </strong>
            </p>
            <p className="small muted">
              Точный календарный график создаётся системой в момент активации программы и
              доступен в личном кабинете.
            </p>
          </Card>
        </div>
        <aside>
          <Card className="purchase-card">
            <h2>Условия программы</h2>
            <dl>
              <div>
                <dt>Стоимость</dt>
                <dd>
                  <MoneyValue value={plan.price} />
                </dd>
              </div>
              <div>
                <dt>Срок доступа</dt>
                <dd>
                  {plan.access_duration_value}{" "}
                  {durationLabels[plan.access_duration_unit]}
                </dd>
              </div>
              <div>
                <dt>Статус</dt>
                <dd>{plan.is_active ? "Доступна" : "Недоступна"}</dd>
              </div>
              {wallet && (
                <div>
                  <dt>Ваш баланс</dt>
                  <dd>
                    <MoneyValue value={wallet.available_balance} />
                  </dd>
                </div>
              )}
            </dl>
            <Button onClick={openPurchase} disabled={!plan.is_active}>
              Купить подписку
            </Button>
            <p className="small muted">
              Условия копируются в купленную подписку и не меняются при
              последующем редактировании плана.
            </p>
          </Card>
        </aside>
      </div>
      <ConfirmDialog
        open={confirmOpen}
        title={enough ? "Подтверждение покупки" : "Недостаточно средств"}
        confirmLabel={enough ? "Купить подписку" : "Пополнить баланс"}
        loading={purchasing}
        onClose={() => setConfirmOpen(false)}
        onConfirm={() =>
          enough ? void purchase() : navigate("/account/deposits")
        }
      >
        {wallet && enough ? (
          <>
            <p>
              Программа: <strong>{plan.title}</strong>
            </p>
            <p>
              Стоимость: <MoneyValue value={plan.price} />
            </p>
            <p>
              Баланс после покупки:{" "}
              <MoneyValue
                value={subtractMoney(wallet.available_balance, plan.price)}
              />
            </p>
            <p>
              Вознаграждение: <MoneyValue value={plan.reward_amount} />{" "}
              {frequencyLabels[plan.reward_frequency]}
            </p>
          </>
        ) : (
          <>
            <p>
              Текущий баланс:{" "}
              <MoneyValue value={wallet?.available_balance ?? "0.000000"} />
            </p>
            <p>
              Стоимость: <MoneyValue value={plan.price} />
            </p>
            <p>
              Не хватает:{" "}
              <MoneyValue
                value={subtractMoney(
                  plan.price,
                  wallet?.available_balance ?? "0.000000",
                )}
              />
            </p>
            <Link className="button button-primary" to="/account/deposits">
              Пополнить баланс
            </Link>
          </>
        )}
      </ConfirmDialog>
    </section>
  );
}
