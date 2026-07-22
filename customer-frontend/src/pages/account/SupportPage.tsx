import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getSystemConfig } from "../../api/system";
import {
  createTicket,
  listTickets,
  uploadAttachments,
} from "../../api/support";
import type { PublicSystemConfig, SupportTicket } from "../../api/types";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { Pagination } from "../../components/Pagination";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";

export function SupportPage() {
  const [search] = useSearchParams();
  const [items, setItems] = useState<SupportTicket[]>([]);
  const [config, setConfig] = useState<PublicSystemConfig | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [category, setCategory] = useState<SupportTicket["category"]>(
    search.get("invoiceId") ? "deposit_problem" : "other",
  );
  const [subject, setSubject] = useState(
    search.get("invoiceId") ? "Проблема с пополнением" : "",
  );
  const [txid, setTxid] = useState("");
  const [reportedAmount, setReportedAmount] = useState("");
  const [description, setDescription] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const invoiceId = search.get("invoiceId") || undefined;
  const expected = search.get("expected");
  function load() {
    setLoading(true);
    Promise.all([listTickets(page, 10), getSystemConfig()])
      .then(([d, c]) => {
        setItems(d.items);
        setTotal(d.total);
        setConfig(c);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(load, [page]);
  function selectFiles(list: FileList | null) {
    const next = Array.from(list ?? []);
    const max = config?.support_max_files_per_message ?? 3;
    const maxBytes = (config?.support_max_file_size_mb ?? 5) * 1024 * 1024;
    if (next.length > max) {
      showToast(`Можно выбрать не более ${max} файлов`, "error");
      return;
    }
    if (next.some((file) => file.size > maxBytes)) {
      showToast(
        `Размер одного файла не должен превышать ${config?.support_max_file_size_mb ?? 5} MB`,
        "error",
      );
      return;
    }
    setFiles(next);
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const amountLine = reportedAmount
        ? `Фактически отправленная сумма: ${reportedAmount} USDT\n`
        : "";
      const expectedLine = expected
        ? `Ожидаемая точная сумма: ${expected} USDT\n`
        : "";
      const ticket = await createTicket({
        category,
        subject,
        message: `${expectedLine}${amountLine}\n${description}`.trim(),
        ...(txid ? { txid } : {}),
        ...(invoiceId ? { related_deposit_invoice_id: invoiceId } : {}),
      });
      const first = ticket.messages[0];
      if (files.length && first) await uploadAttachments(first.id, files);
      showToast("Обращение создано", "success");
      navigate(`/account/support/${ticket.id}`);
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось создать обращение",
        "error",
      );
    } finally {
      setSubmitting(false);
    }
  }
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Помощь</p>
          <h1>Обращения в поддержку</h1>
        </div>
      </div>
      <div className="two-column align-start">
        <Card>
          <h2>Новое обращение</h2>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Категория
              <select
                value={category}
                onChange={(e) =>
                  setCategory(e.target.value as SupportTicket["category"])
                }
              >
                <option value="deposit_problem">Проблема с пополнением</option>
                <option value="withdrawal_problem">Проблема с выводом</option>
                <option value="subscription_problem">
                  Проблема с подпиской
                </option>
                <option value="other">Другое</option>
              </select>
            </label>
            <label>
              Тема
              <input
                required
                minLength={3}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
            </label>
            {category === "deposit_problem" && (
              <>
                <label>
                  TxID
                  <input
                    required
                    pattern="[0-9a-fA-F]{64}"
                    placeholder="64 шестнадцатеричных символа"
                    value={txid}
                    onChange={(e) => setTxid(e.target.value)}
                  />
                </label>
                <label>
                  Фактически отправленная сумма
                  <input
                    inputMode="decimal"
                    value={reportedAmount}
                    onChange={(e) => setReportedAmount(e.target.value)}
                    placeholder="100.000000"
                  />
                  <span className="field-hint">
                    В системе нет отдельного поля: значение будет сохранено в
                    первом сообщении.
                  </span>
                </label>
              </>
            )}
            <label>
              Описание
              <textarea
                required
                minLength={3}
                rows={5}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <label>
              Вложения
              <input
                type="file"
                multiple
                accept=".png,.jpg,.jpeg,.webp,.pdf,image/png,image/jpeg,image/webp,application/pdf"
                onChange={(e) => selectFiles(e.target.files)}
              />
              <span className="field-hint">
                До {config?.support_max_files_per_message ?? 3} файлов, до{" "}
                {config?.support_max_file_size_mb ?? 5} MB каждый.
              </span>
            </label>
            {files.length > 0 && (
              <ul className="file-list">
                {files.map((file) => (
                  <li key={`${file.name}-${file.size}`}>{file.name}</li>
                ))}
              </ul>
            )}
            <Button type="submit" loading={submitting}>
              Создать обращение
            </Button>
          </form>
        </Card>
        <Card>
          <h2>Что подготовить</h2>
          <ul className="check-list">
            <li>TxID из Binance или Bybit</li>
            <li>Фактическую сумму перевода</li>
            <li>ID связанной заявки</li>
            <li>Скриншот или PDF подтверждения</li>
          </ul>
          <p>
            Сообщение пользователя не зачисляет баланс автоматически.
            Администратор проверяет реальный BinanceDeposit.
          </p>
        </Card>
      </div>
      <h2>Мои обращения</h2>
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
                  <th>Дата</th>
                  <th>Тема</th>
                  <th>Категория</th>
                  <th>Статус</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>{item.subject}</td>
                    <td>{item.category}</td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>
                      <Link to={`/account/support/${item.id}`}>Открыть</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={page}
            pageSize={10}
            total={total}
            onChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          title="Обращений пока нет"
          text="Используйте форму, если автоматическая операция не завершилась."
        />
      )}
    </div>
  );
}
