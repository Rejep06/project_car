import { Download } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addTicketMessage,
  downloadAttachment,
  getTicket,
  uploadAttachments,
} from "../../api/support";
import type { SupportTicket } from "../../api/types";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";

export function SupportDetailsPage() {
  const { id = "" } = useParams();
  const [ticket, setTicket] = useState<SupportTicket | null>(null);
  const [message, setMessage] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const load = useCallback(
    () =>
      getTicket(id)
        .then(setTicket)
        .catch((e: Error) => setError(e.message)),
    [id],
  );
  useEffect(() => {
    void load();
  }, [load]);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const created = await addTicketMessage(id, message);
      if (files.length) await uploadAttachments(created.id, files);
      setMessage("");
      setFiles([]);
      await load();
      showToast("Сообщение отправлено", "success");
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось отправить сообщение",
        "error",
      );
    } finally {
      setSubmitting(false);
    }
  }
  async function download(attachmentId: string, name: string) {
    try {
      const blob = await downloadAttachment(attachmentId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = name;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось скачать файл",
        "error",
      );
    }
  }
  if (error) return <div className="notice danger">{error}</div>;
  if (!ticket) return <LoadingSpinner />;
  return (
    <div className="account-page">
      <Link to="/account/support">← Все обращения</Link>
      <div className="page-title">
        <div>
          <p className="eyebrow">Обращение</p>
          <h1>{ticket.subject}</h1>
        </div>
        <StatusBadge status={ticket.status} />
      </div>
      {ticket.txid_conflict && (
        <div className="notice warning">
          TxID требует дополнительной проверки. Данные другого пользователя не
          раскрываются.
        </div>
      )}
      <div className="message-thread">
        {ticket.messages.map((item) => (
          <Card key={item.id} className="message-card">
            <div className="message-meta">
              <strong>{item.author_email}</strong>
              <span>{formatDate(item.created_at)}</span>
            </div>
            <p className="pre-wrap">{item.message}</p>
            {item.txid && (
              <p className="break-all">
                <strong>TxID:</strong> {item.txid}
              </p>
            )}
            {item.attachments.length > 0 && (
              <div className="attachment-list">
                {item.attachments.map((attachment) => (
                  <button
                    type="button"
                    key={attachment.id}
                    onClick={() =>
                      void download(attachment.id, attachment.original_filename)
                    }
                  >
                    <Download size={16} />
                    {attachment.original_filename}
                  </button>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>
      {ticket.status !== "closed" && (
        <Card>
          <h2>Добавить сообщение</h2>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Сообщение
              <textarea
                required
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
            </label>
            <label>
              Вложения
              <input
                type="file"
                multiple
                accept=".png,.jpg,.jpeg,.webp,.pdf"
                onChange={(e) =>
                  setFiles(Array.from(e.target.files ?? []).slice(0, 3))
                }
              />
            </label>
            <Button type="submit" loading={submitting}>
              Отправить
            </Button>
          </form>
        </Card>
      )}
    </div>
  );
}
