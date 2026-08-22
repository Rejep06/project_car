import { CheckCircle2, WalletCards } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getSystemConfig } from "../../api/system";
import type {
  DepositInvoice,
  DepositWallet,
  PublicSystemConfig,
} from "../../api/types";
import {
  createDeposit,
  listDeposits,
  listDepositWallets,
} from "../../api/wallet";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";

export function DepositsPage() {
  const [items, setItems] = useState<DepositInvoice[]>([]);
  const [wallets, setWallets] = useState<DepositWallet[]>([]);
  const [selectedWalletId, setSelectedWalletId] = useState("");
  const [config, setConfig] = useState<PublicSystemConfig | null>(null);
  const [amount, setAmount] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const selectedWallet = wallets.find((wallet) => wallet.id === selectedWalletId);

  function load() {
    setLoading(true);
    Promise.all([
      listDeposits(page, 10),
      listDepositWallets(),
      getSystemConfig(),
    ])
      .then(([deposits, addresses, systemConfig]) => {
        setItems(deposits.items);
        setTotal(deposits.total);
        setWallets(addresses);
        setSelectedWalletId((current) =>
          addresses.some((wallet) => wallet.id === current)
            ? current
            : addresses[0]?.id || "",
        );
        setConfig(systemConfig);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [page]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedWalletId) {
      showToast("Выберите кошелёк для пополнения", "error");
      return;
    }
    setCreating(true);
    try {
      const invoice = await createDeposit(amount, selectedWalletId);
      showToast("Заявка на пополнение создана", "success");
      navigate(`/account/deposits/${invoice.id}`);
    } catch (e) {
      showToast(
        e instanceof Error ? e.message : "Не удалось создать заявку",
        "error",
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">
            {selectedWallet?.asset ?? config?.asset ?? "USDT"} ·{" "}
            {selectedWallet?.network_display_name ?? config?.network ?? "Сеть пополнения"}
          </p>
          <h1>Пополнение баланса</h1>
        </div>
      </div>

      <div className="two-column align-start">
        <Card>
          <h2>Новая заявка</h2>
          <p>
            Выберите удобный кошелёк, укажите сумму и получите реквизиты для
            перевода.
          </p>
          <form className="form-stack" onSubmit={submit}>
            <fieldset className="wallet-choice-fieldset">
              <legend>Кошелёк для пополнения</legend>
              {loading ? (
                <LoadingSpinner />
              ) : wallets.length ? (
                <div className="deposit-wallet-options">
                  {wallets.map((wallet) => (
                    <label
                      key={wallet.id}
                      className={`deposit-wallet-option ${selectedWalletId === wallet.id ? "selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="deposit-wallet"
                        value={wallet.id}
                        checked={selectedWalletId === wallet.id}
                        onChange={() => setSelectedWalletId(wallet.id)}
                      />
                      <WalletCards size={21} />
                      <span>
                        <strong>{wallet.title}</strong>
                        <small>{wallet.network_display_name}</small>
                      </span>
                      {selectedWalletId === wallet.id && <CheckCircle2 size={20} />}
                    </label>
                  ))}
                </div>
              ) : (
                <div className="notice warning">
                  Адреса пополнения временно недоступны. Попробуйте позднее.
                </div>
              )}
            </fieldset>
            <label>
              Сумма пополнения
              <input
                required
                inputMode="decimal"
                placeholder={config?.min_deposit_amount ?? "10.000000"}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
              <span className="field-hint">
                Минимум: {config?.min_deposit_amount ?? "—"} USDT
              </span>
            </label>
            <Button
              type="submit"
              loading={creating}
              disabled={!selectedWalletId}
            >
              Получить реквизиты
            </Button>
          </form>
        </Card>

        <Card>
          <h2>Перед переводом</h2>
          <ul className="check-list">
            <li>
              Используйте только сеть {selectedWallet?.network_display_name ?? config?.network ?? "из выбранных реквизитов"}.
            </li>
            <li>Переведите точную сумму из созданной заявки.</li>
            <li>Проверьте адрес и сумму перед подтверждением.</li>
            <li>Сохраните TxID до зачисления средств.</li>
          </ul>
          <div className="notice info">
            Рекомендуемый срок оплаты заявки — {config?.deposit_invoice_ttl_minutes ?? 30} минут.
          </div>
        </Card>
      </div>

      <h2>Мои заявки</h2>
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
                  <th>Создана</th>
                  <th>Кошелёк</th>
                  <th>Сумма</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>{item.wallet_name}</td>
                    <td><MoneyValue value={item.expected_amount} /></td>
                    <td><StatusBadge status={item.status} /></td>
                    <td><Link to={`/account/deposits/${item.id}`}>Открыть</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={10} total={total} onChange={setPage} />
        </>
      ) : (
        <EmptyState
          title="Заявок пока нет"
          text="Создайте первую заявку, чтобы получить адрес и точную сумму перевода."
        />
      )}
    </div>
  );
}
