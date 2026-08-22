import {
  AlertTriangle,
  ArrowRight,
  ClipboardList,
  CreditCard,
  Headphones,
  Users,
  WalletCards,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listDeposits } from "../api/deposits";
import { listPlans } from "../api/plans";
import { listTickets } from "../api/support";
import { listUsers } from "../api/users";
import { listWithdrawals } from "../api/withdrawals";
import { Card } from "../components/Card";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
interface Metric {
  label: string;
  value: number;
  to: string;
  Icon: typeof Users;
}
export function DashboardPage() {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([
      listUsers(1, 5),
      listPlans(1, 5),
      listDeposits(1, 5),
      listWithdrawals(1, 5),
      listTickets(1, 5),
    ])
      .then(([users, plans, deposits, withdrawals, tickets]) =>
        setMetrics([
          {
            label: "Пользователи",
            value: users.total,
            to: "/users",
            Icon: Users,
          },
          {
            label: "Программы",
            value: plans.total,
            to: "/plans",
            Icon: CreditCard,
          },
          {
            label: "Нераспознанные пополнения",
            value: deposits.total,
            to: "/deposits",
            Icon: WalletCards,
          },
          {
            label: "Заявки на вывод",
            value: withdrawals.total,
            to: "/withdrawals",
            Icon: ClipboardList,
          },
          {
            label: "Обращения",
            value: tickets.total,
            to: "/support",
            Icon: Headphones,
          },
        ]),
      )
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Ошибка загрузки"),
      )
      .finally(() => setLoading(false));
  }, []);
  return (
    <>
      <PageHeader
        title="Обзор"
        description="Быстрый доступ к основным рабочим разделам."
      />
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <Card>
          <p className="form-error">
            <AlertTriangle /> {error}
          </p>
        </Card>
      ) : (
        <div className="metrics-grid">
          {metrics.map(({ label, value, to, Icon }) => (
            <Link className="metric-card" to={to} key={to}>
              <Icon />
              <span>{label}</span>
              <strong>{value}</strong>
              <ArrowRight />
            </Link>
          ))}
        </div>
      )}
      <Card className="dashboard-note">
        <h2>Ключевые показатели</h2>
        <p>
          Используйте карточки выше для быстрого перехода к пользователям,
          программам, пополнениям, выводам и обращениям.
        </p>
      </Card>
    </>
  );
}
