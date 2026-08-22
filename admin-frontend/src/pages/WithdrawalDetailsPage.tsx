import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  approveWithdrawal,
  completeWithdrawal,
  getWithdrawal,
  markSent,
  rejectWithdrawal,
} from "../api/withdrawals";
import type { AdminWithdrawal } from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
import { formatMoney } from "../utils/money";
export function WithdrawalDetailsPage() {
  const { id = "" } = useParams();
  const [item, setItem] = useState<AdminWithdrawal | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<"approve" | "complete" | null>(null);
  const [comment, setComment] = useState("");
  const [txid, setTxid] = useState("");
  const [fee, setFee] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    getWithdrawal(id)
      .then(setItem)
      .catch((e) => setError(e.message));
  }, [id]);
  async function action(fn: () => Promise<AdminWithdrawal>, success: string) {
    setBusy(true);
    setError("");
    try {
      setItem(await fn());
      setMessage(success);
      setConfirm(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  async function reject(e: FormEvent) {
    e.preventDefault();
    await action(
      () => rejectWithdrawal(id, comment),
      "Вывод отклонён, заблокированные средства возвращены",
    );
  }
  async function sent(e: FormEvent) {
    e.preventDefault();
    if (!txid.trim()) {
      setError("Для отметки отправки требуется TxID");
      return;
    }
    await action(
      () => markSent(id, txid, fee, comment),
      "Вывод отмечен отправленным",
    );
  }
  if (!item && !error) return <LoadingSpinner />;
  if (!item) return <p className="form-error">{error}</p>;
  return (
    <>
      <PageHeader
        title="Заявка на вывод"
        description={item.id}
        actions={
          <Link className="button button-secondary" to="/withdrawals">
            Назад
          </Link>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      <div className="detail-grid">
        <Card>
          <h2>Перевод</h2>
          <dl className="details">
            <div>
              <dt>Пользователь</dt>
              <dd>{item.user_email}</dd>
            </div>
            <div>
              <dt>Адрес Ethereum</dt>
              <dd className="mono break-all">{item.destination_address}</dd>
            </div>
            <div>
              <dt>Сумма получателю</dt>
              <dd>
                {formatMoney(item.amount)} {item.asset}
              </dd>
            </div>
            <div>
              <dt>Расчётная комиссия</dt>
              <dd>
                {formatMoney(item.fee)} {item.asset}
              </dd>
            </div>
            <div>
              <dt>Заблокировано</dt>
              <dd>
                {formatMoney(item.held_total)} {item.asset}
              </dd>
            </div>
            <div>
              <dt>Финальное списание</dt>
              <dd>
                {formatMoney(item.final_total)} {item.asset}
              </dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2>Состояние</h2>
          <dl className="details">
            <div>
              <dt>Статус</dt>
              <dd>
                <StatusBadge value={item.status} />
              </dd>
            </div>
            <div>
              <dt>TxID</dt>
              <dd className="mono break-all">{item.txid ?? "—"}</dd>
            </div>
            <div>
              <dt>Комментарий</dt>
              <dd>{item.admin_comment ?? "—"}</dd>
            </div>
            <div>
              <dt>Подтверждён</dt>
              <dd>{formatDateTime(item.approved_at)}</dd>
            </div>
            <div>
              <dt>Отправлен</dt>
              <dd>{formatDateTime(item.sent_at)}</dd>
            </div>
            <div>
              <dt>Завершён</dt>
              <dd>{formatDateTime(item.completed_at)}</dd>
            </div>
          </dl>
        </Card>
      </div>
      {item.status === "pending_review" && (
        <div className="action-grid">
          <Card>
            <h2>Подтвердить</h2>
            <p>
              Проверьте сумму, адрес и доступность реквизитов перед подтверждением.
            </p>
            <Button onClick={() => setConfirm("approve")}>
              Подтвердить заявку
            </Button>
          </Card>
          <Card>
            <h2>Отклонить</h2>
            <form onSubmit={reject}>
              <FormField label="Причина">
                <textarea
                  rows={3}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  minLength={3}
                  required
                />
              </FormField>
              <Button variant="danger" type="submit" loading={busy}>
                Отклонить
              </Button>
            </form>
          </Card>
        </div>
      )}
      {item.status === "approved" && (
        <Card>
          <h2>Отметить отправленным</h2>
          <form className="form-grid" onSubmit={sent}>
            <FormField label="TxID">
              <input
                value={txid}
                onChange={(e) => setTxid(e.target.value)}
                required
              />
            </FormField>
            <FormField label="Фактическая комиссия, USDT">
              <input
                inputMode="decimal"
                value={fee}
                onChange={(e) => setFee(e.target.value)}
                required
              />
            </FormField>
            <FormField label="Комментарий">
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
              />
            </FormField>
            <div className="form-actions">
              <Button type="submit" loading={busy}>
                Отметить отправленным
              </Button>
            </div>
          </form>
        </Card>
      )}
      {item.status === "sent" && (
        <Card>
          <h2>Завершение</h2>
          <p>
            Убедитесь, что транзакция подтверждена. После завершения
            заблокированная сумма будет окончательно списана.
          </p>
          <FormField label="Комментарий">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
            />
          </FormField>
          <Button onClick={() => setConfirm("complete")}>
            Завершить вывод
          </Button>
        </Card>
      )}
      <ConfirmDialog
        open={confirm === "approve"}
        title="Подтвердить заявку"
        description="Средства останутся заблокированными до ручной отправки и завершения."
        onConfirm={() =>
          action(() => approveWithdrawal(id), "Заявка подтверждена")
        }
        loading={busy}
        onClose={() => setConfirm(null)}
      />
      <ConfirmDialog
        open={confirm === "complete"}
        title="Завершить вывод"
        description={`TxID: ${item.txid ?? "не указан"}. Проверьте перевод перед завершением заявки.`}
        onConfirm={() =>
          action(() => completeWithdrawal(id, comment), "Вывод завершён")
        }
        loading={busy}
        onClose={() => setConfirm(null)}
      />
    </>
  );
}
