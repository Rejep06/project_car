import {
  CreditCard,
  FileText,
  Gift,
  Headphones,
  ReceiptText,
  WalletCards,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listSubscriptions } from "../../api/subscriptions";
import { listTickets } from "../../api/support";
import type {
  SupportTicket,
  UserSubscription,
  Wallet,
  WalletTransaction,
  Withdrawal,
} from "../../api/types";
import { getWallet, listTransactions, listWithdrawals } from "../../api/wallet";
import { Card } from "../../components/Card";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../utils/date";

interface Data {
  wallet: Wallet;
  subscriptions: UserSubscription[];
  subscriptionTotal: number;
  transactions: WalletTransaction[];
  withdrawals: Withdrawal[];
  withdrawalTotal: number;
  tickets: SupportTicket[];
  ticketTotal: number;
}
export function AccountDashboardPage() {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([
      getWallet(),
      listSubscriptions(1, 5),
      listTransactions(1, 5),
      listWithdrawals(1, 5),
      listTickets(1, 5),
    ])
      .then(([wallet, subs, tx, withdrawals, tickets]) =>
        setData({
          wallet,
          subscriptions: subs.items,
          subscriptionTotal: subs.total,
          transactions: tx.items,
          withdrawals: withdrawals.items,
          withdrawalTotal: withdrawals.total,
          tickets: tickets.items,
          ticketTotal: tickets.total,
        }),
      )
      .catch((e: Error) => setError(e.message));
  }, []);
  if (error) return <div className="notice danger">{error}</div>;
  if (!data) return <LoadingSpinner />;
  const nextReward = data.subscriptions
    .flatMap((s) => s.reward_payouts)
    .filter((p) => p.status === "pending")
    .sort((a, b) => a.due_at.localeCompare(b.due_at))[0];
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Личный кабинет</p>
          <h1>Обзор</h1>
        </div>
      </div>
      <div className="dashboard-grid">
        <Card className="metric-card">
          <span>Доступный баланс</span>
          <strong>
            <MoneyValue value={data.wallet.available_balance} />
          </strong>
          <Link to="/account/deposits">Пополнить</Link>
        </Card>
        <Card className="metric-card">
          <span>Заблокировано</span>
          <strong>
            <MoneyValue value={data.wallet.locked_balance} />
          </strong>
          <Link to="/account/withdrawals">Выводы</Link>
        </Card>
        <Card className="metric-card">
          <span>Программы</span>
          <strong>{data.subscriptionTotal}</strong>
          <Link to="/account/subscriptions">Открыть</Link>
        </Card>
        <Card className="metric-card">
          <span>Ближайшее вознаграждение</span>
          <strong>
            {nextReward ? (
              <MoneyValue value={nextReward.amount} />
            ) : (
              "Нет данных"
            )}
          </strong>
          <span>
            {nextReward
              ? formatDate(nextReward.due_at)
              : "Откройте программу для полного графика"}
          </span>
        </Card>
      </div>
      <div className="quick-actions">
        <Link to="/account/deposits">
          <CreditCard />
          Пополнить баланс
        </Link>
        <Link to="/account/withdrawals">
          <ReceiptText />
          Вывести средства
        </Link>
        <Link to="/plans">
          <FileText />
          Посмотреть программы
        </Link>
        <Link to="/account/support">
          <Headphones />
          Написать в поддержку
        </Link>
      </div>
      <div className="two-column">
        <Card>
          <div className="card-heading">
            <h2>Последние операции</h2>
            <Link to="/account/transactions">Все</Link>
          </div>
          {data.transactions.length ? (
            <div className="compact-list">
              {data.transactions.map((tx) => (
                <div key={tx.id}>
                  <div>
                    <StatusBadge status={tx.operation_type} />
                    <p>{tx.description}</p>
                  </div>
                  <div>
                    <MoneyValue value={tx.available_delta} signed />
                    <span>{formatDate(tx.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">Операций пока нет.</p>
          )}
        </Card>
        <Card>
          <div className="card-heading">
            <h2>Текущие задачи</h2>
          </div>
          <div className="summary-links">
            <Link to="/account/withdrawals">
              <WalletCards />
              Заявок на вывод: {data.withdrawalTotal}
            </Link>
            <Link to="/account/support">
              <Headphones />
              Обращений: {data.ticketTotal}
            </Link>
            <Link to="/account/rewards">
              <Gift />
              История вознаграждений
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
