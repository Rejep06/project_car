import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Wallet, WalletTransaction } from "../../api/types";
import { getWallet, listTransactions } from "../../api/wallet";
import { Card } from "../../components/Card";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../utils/date";

export function WalletPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([getWallet(), listTransactions(1, 10)])
      .then(([w, t]) => {
        setWallet(w);
        setTransactions(t.items);
      })
      .catch((e: Error) => setError(e.message));
  }, []);
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Внутренний баланс</p>
          <h1>Кошелёк</h1>
        </div>
        <div className="page-actions">
          <Link className="button button-primary" to="/account/deposits">
            Пополнить
          </Link>
          <Link className="button button-secondary" to="/account/withdrawals">
            Вывести
          </Link>
        </div>
      </div>
      {error ? (
        <div className="notice danger">{error}</div>
      ) : !wallet ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="wallet-cards">
            <Card>
              <span>Доступно</span>
              <strong>
                <MoneyValue value={wallet.available_balance} />
              </strong>
              <p>
                Можно потратить на подписку или включить в новую заявку на
                вывод.
              </p>
            </Card>
            <Card>
              <span>Заблокировано</span>
              <strong>
                <MoneyValue value={wallet.locked_balance} />
              </strong>
              <p>Средства в заявках на ручной вывод.</p>
            </Card>
          </div>
          <Card>
            <div className="card-heading">
              <h2>Последние операции</h2>
              <Link to="/account/transactions">Полная история</Link>
            </div>
            {transactions.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Тип</th>
                      <th>Описание</th>
                      <th>Доступный баланс</th>
                      <th>Дата</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>
                          <StatusBadge status={tx.operation_type} />
                        </td>
                        <td>{tx.description}</td>
                        <td>
                          <MoneyValue value={tx.available_delta} signed />
                        </td>
                        <td>{formatDate(tx.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted">Операций пока нет.</p>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
