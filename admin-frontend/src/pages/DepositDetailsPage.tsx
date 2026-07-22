import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { assignDeposit, getDeposit, ignoreDeposit } from "../api/deposits";
import type { UnmatchedDeposit } from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";
export function DepositDetailsPage() {
  const { id = "" } = useParams();
  const [item, setItem] = useState<UnmatchedDeposit | null>(null);
  const [userId, setUserId] = useState("");
  const [invoiceId, setInvoiceId] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    getDeposit(id)
      .then(setItem)
      .catch((e) => setError(e.message));
  }, [id]);
  async function performAssign() {
    setBusy(true);
    try {
      setItem(await assignDeposit(id, userId, invoiceId || undefined));
      setMessage("Фактически полученная сумма зачислена безопасно");
      setConfirm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка зачисления");
    } finally {
      setBusy(false);
    }
  }
  async function ignore() {
    setBusy(true);
    try {
      setItem(await ignoreDeposit(id));
      setMessage("Запись помечена как игнорируемая");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  if (!item && !error) return <LoadingSpinner />;
  if (!item) return <p className="form-error">{error}</p>;
  return (
    <>
      <PageHeader
        title="Нераспознанное пополнение"
        description={item.id}
        actions={
          <Link className="button button-secondary" to="/deposits">
            Назад
          </Link>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      <div className="detail-grid">
        <Card>
          <h2>Данные депозита</h2>
          <dl className="details">
            <div>
              <dt>TxID</dt>
              <dd className="mono break-all">{item.txid}</dd>
            </div>
            <div>
              <dt>Binance deposit ID</dt>
              <dd className="mono break-all">{item.binance_deposit_id}</dd>
            </div>
            <div>
              <dt>Монета</dt>
              <dd>{item.coin}</dd>
            </div>
            <div>
              <dt>Фактическая сумма</dt>
              <dd>{formatMoney(item.amount)} USDT</dd>
            </div>
            <div>
              <dt>Адрес проекта</dt>
              <dd className="mono break-all">{item.address}</dd>
            </div>
            <div>
              <dt>Сеть</dt>
              <dd>{item.network}</dd>
            </div>
            <div>
              <dt>Статус Binance</dt>
              <dd>{item.binance_status}</dd>
            </div>
            <div>
              <dt>Время депозита</dt>
              <dd>{formatDateTime(item.deposit_time)}</dd>
            </div>
            <div>
              <dt>TxID уже зачислен</dt>
              <dd>{item.txid_already_used ? "Да" : "Нет"}</dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2>Разбор</h2>
          <dl className="details">
            <div>
              <dt>Причина</dt>
              <dd>{label(item.reason)}</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>
                <StatusBadge value={item.status} />
              </dd>
            </div>
            <div>
              <dt>Назначенный пользователь</dt>
              <dd className="mono">{item.assigned_user_id ?? "—"}</dd>
            </div>
            <div>
              <dt>Назначенная заявка</dt>
              <dd className="mono">{item.assigned_invoice_id ?? "—"}</dd>
            </div>
            <div>
              <dt>Назначено</dt>
              <dd>{formatDateTime(item.assigned_at)}</dd>
            </div>
          </dl>
        </Card>
      </div>
      {item.status === "unresolved" && (
        <Card>
          <h2>Ручное зачисление</h2>
          <p className="muted">
            Endpoint повторно проверяет USDT, TRON, адрес, успешный
            Binance-статус, уникальность Binance deposit ID и TxID. Баланс
            изменяется через WalletService с idempotency key{" "}
            <code>manual-deposit:{item.binance_deposit_id}</code>.
          </p>
          <form
            className="inline-form"
            onSubmit={(e) => {
              e.preventDefault();
              setConfirm(true);
            }}
          >
            <FormField label="UUID пользователя">
              <input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                required
              />
            </FormField>
            <FormField label="UUID заявки (необязательно)">
              <input
                value={invoiceId}
                onChange={(e) => setInvoiceId(e.target.value)}
              />
            </FormField>
            <Button type="submit">Зачислить фактическую сумму</Button>
            <Button
              type="button"
              variant="secondary"
              loading={busy}
              onClick={ignore}
            >
              Игнорировать
            </Button>
          </form>
        </Card>
      )}
      <ConfirmDialog
        open={confirm}
        title="Подтвердить ручное зачисление"
        description={`Пользователь: ${userId}. Фактическая сумма: ${formatMoney(item.amount)} USDT. TxID: ${item.txid}.`}
        confirmLabel="Зачислить"
        loading={busy}
        onConfirm={performAssign}
        onClose={() => setConfirm(false)}
      />
    </>
  );
}
