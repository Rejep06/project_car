import { Download } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addMessage,
  downloadAttachment,
  getTicket,
  resolveDeposit,
  updateStatus,
} from "../api/support";
import type { AdminTicket } from "../api/types";
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
export function SupportDetailsPage() {
  const { id = "" } = useParams();
  const [ticket, setTicket] = useState<AdminTicket | null>(null);
  const [reply, setReply] = useState("");
  const [status, setStatus] = useState<AdminTicket["status"]>("in_review");
  const [invoiceId, setInvoiceId] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(
    () =>
      getTicket(id)
        .then((t) => {
          setTicket(t);
          setStatus(t.status);
        })
        .catch((e) => setError(e.message)),
    [id],
  );
  useEffect(() => {
    void load();
  }, [load]);
  async function send(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await addMessage(id, reply);
      setReply("");
      setMessage("Ответ отправлен");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  async function change() {
    setBusy(true);
    try {
      setTicket(await updateStatus(id, status));
      setMessage("Статус изменён");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  async function resolve() {
    setBusy(true);
    try {
      setTicket(await resolveDeposit(id, invoiceId || undefined));
      setMessage("Депозит зачислен и обращение обновлено");
      setConfirm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка зачисления");
    } finally {
      setBusy(false);
    }
  }
  async function download(attachmentId: string, name: string) {
    try {
      const blob = await downloadAttachment(attachmentId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка скачивания");
    }
  }
  if (!ticket && !error) return <LoadingSpinner />;
  if (!ticket) return <p className="form-error">{error}</p>;
  return (
    <>
      <PageHeader
        title={ticket.subject}
        description={`Пользователь: ${ticket.user_email}`}
        actions={
          <Link className="button button-secondary" to="/support">
            Назад
          </Link>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      {(ticket.warning || ticket.txid_conflict || ticket.txid_already_used) && (
        <Card className="warning-card">
          <h2>Предупреждение</h2>
          <p>{ticket.warning || "Возможный конфликт: TxID уже использован."}</p>
          <p>
            Данные другого пользователя не отображаются в клиентском интерфейсе.
          </p>
        </Card>
      )}
      <div className="detail-grid">
        <Card>
          <h2>Обращение</h2>
          <dl className="details">
            <div>
              <dt>Категория</dt>
              <dd>{label(ticket.category)}</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>
                <StatusBadge value={ticket.status} />
              </dd>
            </div>
            <div>
              <dt>Связанная заявка</dt>
              <dd className="mono">
                {ticket.related_deposit_invoice_id ?? "—"}
              </dd>
            </div>
            <div>
              <dt>Ожидаемая сумма</dt>
              <dd>
                {ticket.expected_amount
                  ? `${formatMoney(ticket.expected_amount)} USDT`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>Фактическая сумма</dt>
              <dd>
                {ticket.actual_amount
                  ? `${formatMoney(ticket.actual_amount)} USDT`
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>Создано</dt>
              <dd>{formatDateTime(ticket.created_at)}</dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2>Данные блокчейн-перевода</h2>
          <dl className="details">
            <div>
              <dt>ID события</dt>
              <dd className="mono break-all">
                {ticket.deposit_event_id ?? "—"}
              </dd>
            </div>
            <div>
              <dt>TxID</dt>
              <dd className="mono break-all">{ticket.deposit_txid ?? "—"}</dd>
            </div>
            <div>
              <dt>Сеть</dt>
              <dd>{ticket.deposit_network ?? "—"}</dd>
            </div>
            <div>
              <dt>Адрес</dt>
              <dd className="mono break-all">
                {ticket.deposit_address ?? "—"}
              </dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>{ticket.deposit_status ?? "—"}</dd>
            </div>
            <div>
              <dt>Время депозита</dt>
              <dd>{formatDateTime(ticket.deposit_detected_at)}</dd>
            </div>
          </dl>
          {ticket.deposit_raw_data && (
            <details>
              <summary>Исходные нормализованные данные</summary>
              <pre>{JSON.stringify(ticket.deposit_raw_data, null, 2)}</pre>
            </details>
          )}
        </Card>
      </div>
      <Card>
        <h2>История сообщений</h2>
        <div className="messages">
          {ticket.messages.map((m) => (
            <article key={m.id}>
              <header>
                <strong>{m.author_email}</strong>
                <time>{formatDateTime(m.created_at)}</time>
              </header>
              <p>{m.message}</p>
              {m.txid && <p className="mono">TxID: {m.txid}</p>}
              {m.attachments.length > 0 && (
                <div className="attachments">
                  {m.attachments.map((a) => (
                    <button
                      type="button"
                      key={a.id}
                      onClick={() => download(a.id, a.original_filename)}
                    >
                      <Download />
                      {a.original_filename} ({Math.ceil(a.size_bytes / 1024)}{" "}
                      КБ)
                    </button>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
        <form onSubmit={send}>
          <FormField label="Ответ администратора">
            <textarea
              rows={4}
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              required
            />
          </FormField>
          <Button type="submit" loading={busy}>
            Ответить
          </Button>
        </form>
      </Card>
      <div className="action-grid">
        <Card>
          <h2>Статус</h2>
          <FormField label="Новый статус">
            <select
              value={status}
              onChange={(e) =>
                setStatus(e.target.value as AdminTicket["status"])
              }
            >
              {["open", "in_review", "waiting_user", "resolved", "closed"].map(
                (x) => (
                  <option key={x} value={x}>
                    {label(x)}
                  </option>
                ),
              )}
            </select>
          </FormField>
          <Button onClick={change} loading={busy}>
            Изменить статус
          </Button>
        </Card>
        {ticket.category === "deposit_problem" && ticket.deposit_event_id && (
          <Card>
            <h2>Зачислить депозит</h2>
            <p className="muted">
              Проверьте данные платежа и зачислите фактически полученную сумму.
            </p>
            <FormField label="UUID заявки (необязательно)">
              <input
                value={invoiceId}
                onChange={(e) => setInvoiceId(e.target.value)}
              />
            </FormField>
            <Button onClick={() => setConfirm(true)}>Зачислить депозит</Button>
          </Card>
        )}
      </div>
      <ConfirmDialog
        open={confirm}
        title="Зачислить фактическую сумму"
        description={`Пользователь: ${ticket.user_email}. TxID: ${ticket.deposit_txid ?? "—"}. Проверьте сумму и реквизиты перед подтверждением.`}
        confirmLabel="Зачислить"
        loading={busy}
        onConfirm={resolve}
        onClose={() => setConfirm(false)}
      />
    </>
  );
}
