import {
  CheckCircle2,
  Dice5,
  Gift,
  Plus,
  Save,
  Search,
  Send,
  Ticket,
  Trash2,
  Trophy,
  UserCheck,
  XCircle,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  confirmAllLotteryWinners,
  confirmLotteryWinner,
  createLottery,
  createLotteryPrize,
  deleteLotteryPrize,
  drawLotteryRandom,
  getLottery,
  listLotteryTickets,
  publishLottery,
  removeLotteryWinner,
  selectLotteryWinnerManually,
  updateLottery,
  updateLotteryPrize,
} from "../api/lotteries";
import type {
  LotteryAdmin,
  LotteryAdminTicket,
  LotteryInput,
  LotteryPrize,
  LotteryPrizeInput,
  LotteryPrizeType,
} from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";

function localDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

function defaultLocalDate(minutesFromNow: number): string {
  return localDateTime(new Date(Date.now() + minutesFromNow * 60_000).toISOString());
}

function isoDate(value: string): string {
  return new Date(value).toISOString();
}

const emptyLottery: LotteryInput = {
  title: "",
  description: "",
  cover_image_url: null,
  ticket_price: "10.000000",
  sales_start_at: defaultLocalDate(10),
  sales_end_at: defaultLocalDate(7 * 24 * 60),
  draw_at: defaultLocalDate(7 * 24 * 60 + 60),
  max_tickets_total: null,
  max_tickets_per_user: 20,
  manager_telegram: null,
  rules_text:
    "Каждый билет участвует только в этой лотерее. Победители определяются после завершения продаж случайным способом, если иной метод прямо не раскрыт в этих правилах до начала продаж. Результат вступает в силу после проверки и подтверждения администратором. Укажите порядок замены недопущенного победителя, срок обращения за призом, налоги, доставку, условия отмены и возврата.",
  rules_version: "1.0",
};

const emptyPrize: LotteryPrizeInput = {
  title: "",
  description: "",
  prize_type: "balance",
  amount: "10.000000",
  quantity: 1,
  sort_order: 0,
  image_url: null,
  manager_telegram: null,
};

export function LotteryFormPage() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const [form, setForm] = useState<LotteryInput>(emptyLottery);
  const [lottery, setLottery] = useState<LotteryAdmin | null>(null);
  const [tickets, setTickets] = useState<LotteryAdminTicket[]>([]);
  const [ticketSearch, setTicketSearch] = useState("");
  const [ticketSearchLoading, setTicketSearchLoading] = useState(false);
  const [prizeForm, setPrizeForm] = useState<LotteryPrizeInput>(emptyPrize);
  const [editingPrizeId, setEditingPrizeId] = useState<string | null>(null);
  const [manualPrizeId, setManualPrizeId] = useState("");
  const [manualTicketId, setManualTicketId] = useState("");
  const [confirmationNote, setConfirmationNote] = useState("");
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    if (isNew || !id) return;
    setLoading(true);
    setError("");
    try {
      const [detail, ticketPage] = await Promise.all([
        getLottery(id),
        listLotteryTickets(id, 1, 100),
      ]);
      setLottery(detail);
      setTickets(ticketPage.items);
      setForm({
        title: detail.title,
        description: detail.description,
        cover_image_url: detail.cover_image_url,
        ticket_price: detail.ticket_price,
        sales_start_at: localDateTime(detail.sales_start_at),
        sales_end_at: localDateTime(detail.sales_end_at),
        draw_at: localDateTime(detail.draw_at),
        max_tickets_total: detail.max_tickets_total,
        max_tickets_per_user: detail.max_tickets_per_user,
        manager_telegram: detail.manager_telegram,
        rules_text: detail.rules_text,
        rules_version: detail.rules_version,
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось загрузить лотерею");
    } finally {
      setLoading(false);
    }
  }, [id, isNew]);

  useEffect(() => {
    void load();
  }, [load]);

  const remainingPrizes = useMemo(() => {
    if (!lottery) return [];
    const counts = new Map<string, number>();
    for (const winner of lottery.admin_winners) {
      if (winner.status !== "cancelled") {
        counts.set(winner.prize_id, (counts.get(winner.prize_id) || 0) + 1);
      }
    }
    return lottery.prizes.filter(
      (prize) => (counts.get(prize.id) || 0) < prize.quantity,
    );
  }, [lottery]);

  const prizesLocked = (lottery?.tickets_sold ?? 0) > 0;

  const availableTickets = useMemo(
    () => tickets.filter((ticket) => ticket.status === "active" && !ticket.is_winner),
    [tickets],
  );

  function updateField<K extends keyof LotteryInput>(key: K, value: LotteryInput[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function searchTickets(event?: FormEvent) {
    event?.preventDefault();
    if (!id) return;
    setTicketSearchLoading(true);
    setError("");
    try {
      const page = await listLotteryTickets(id, 1, 100, ticketSearch);
      setTickets(page.items);
      setManualTicketId("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось найти билеты");
    } finally {
      setTicketSearchLoading(false);
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const payload: LotteryInput = {
        ...form,
        title: form.title.trim(),
        description: form.description.trim(),
        cover_image_url: form.cover_image_url?.trim() || null,
        sales_start_at: isoDate(form.sales_start_at),
        sales_end_at: isoDate(form.sales_end_at),
        draw_at: isoDate(form.draw_at),
        manager_telegram: form.manager_telegram?.trim() || null,
        rules_text: form.rules_text.trim(),
        rules_version: form.rules_version.trim(),
      };
      if (isNew) {
        const created = await createLottery(payload);
        setMessage("Лотерея создана. Теперь добавьте призы.");
        navigate(`/lotteries/${created.id}`, { replace: true });
      } else if (id) {
        await updateLottery(id, payload);
        setMessage("Лотерея сохранена");
        await load();
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось сохранить лотерею");
    } finally {
      setSaving(false);
    }
  }

  function beginPrizeEdit(prize: LotteryPrize) {
    setEditingPrizeId(prize.id);
    setPrizeForm({
      title: prize.title,
      description: prize.description,
      prize_type: prize.prize_type,
      amount: prize.amount,
      quantity: prize.quantity,
      sort_order: prize.sort_order,
      image_url: prize.image_url,
      manager_telegram: prize.manager_telegram,
    });
    document.getElementById("lottery-prize-form")?.scrollIntoView({ behavior: "smooth" });
  }

  function resetPrizeForm() {
    setEditingPrizeId(null);
    setPrizeForm(emptyPrize);
  }

  async function savePrize(event: FormEvent) {
    event.preventDefault();
    if (!id) return;
    setActionLoading("prize");
    setError("");
    try {
      const payload: LotteryPrizeInput = {
        ...prizeForm,
        title: prizeForm.title.trim(),
        description: prizeForm.description.trim(),
        amount: prizeForm.prize_type === "balance" ? prizeForm.amount : null,
        image_url: prizeForm.image_url?.trim() || null,
        manager_telegram: prizeForm.manager_telegram?.trim() || null,
      };
      if (editingPrizeId) {
        await updateLotteryPrize(id, editingPrizeId, payload);
        setMessage("Приз обновлён");
      } else {
        await createLotteryPrize(id, payload);
        setMessage("Приз добавлен");
      }
      resetPrizeForm();
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось сохранить приз");
    } finally {
      setActionLoading("");
    }
  }

  async function removePrize(prize: LotteryPrize) {
    if (!id || !window.confirm(`Удалить приз «${prize.title}»?`)) return;
    setActionLoading(`delete-prize-${prize.id}`);
    try {
      await deleteLotteryPrize(id, prize.id);
      setMessage("Приз удалён");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось удалить приз");
    } finally {
      setActionLoading("");
    }
  }

  async function publish() {
    if (!id || !window.confirm("Опубликовать лотерею и открыть её для пользователей в указанный период?")) return;
    setActionLoading("publish");
    try {
      await publishLottery(id);
      setMessage("Лотерея опубликована");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось опубликовать лотерею");
    } finally {
      setActionLoading("");
    }
  }

  async function drawRandom() {
    if (!id || !window.confirm("Случайно выбрать победителей для всех свободных призовых мест?")) return;
    setActionLoading("draw");
    try {
      await drawLotteryRandom(id);
      setMessage("Кандидаты в победители выбраны. Подтвердите выдачу призов.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось провести случайный выбор");
    } finally {
      setActionLoading("");
    }
  }

  async function manualWinner(event: FormEvent) {
    event.preventDefault();
    if (!id || !manualPrizeId || !manualTicketId) return;
    setActionLoading("manual");
    try {
      await selectLotteryWinnerManually(id, manualPrizeId, manualTicketId);
      setManualPrizeId("");
      setManualTicketId("");
      setMessage("Победитель выбран вручную и ожидает подтверждения");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось выбрать победителя");
    } finally {
      setActionLoading("");
    }
  }

  async function confirmWinner(winnerId: string) {
    setActionLoading(`confirm-${winnerId}`);
    try {
      await confirmLotteryWinner(winnerId, confirmationNote);
      setMessage("Победитель подтверждён, приз передан в обработку");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось подтвердить победителя");
    } finally {
      setActionLoading("");
    }
  }

  async function removeWinner(winnerId: string) {
    if (!window.confirm("Отменить этот выбор победителя?")) return;
    setActionLoading(`remove-${winnerId}`);
    try {
      await removeLotteryWinner(winnerId);
      setMessage("Выбор победителя отменён");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось отменить выбор");
    } finally {
      setActionLoading("");
    }
  }

  async function confirmAll() {
    if (!id || !window.confirm("Подтвердить всех ожидающих победителей? Денежные призы сразу поступят на баланс.")) return;
    setActionLoading("confirm-all");
    try {
      await confirmAllLotteryWinners(id);
      setMessage("Все выбранные победители подтверждены");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось подтвердить победителей");
    } finally {
      setActionLoading("");
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <>
      <PageHeader
        title={isNew ? "Новая лотерея" : lottery?.title || "Лотерея"}
        description="Сначала сохраните условия, затем добавьте призы и опубликуйте лотерею."
        actions={
          <div className="page-actions">
            <Link className="button button-secondary" to="/lotteries">К списку</Link>
            {!isNew && lottery?.status === "draft" ? (
              <Button loading={actionLoading === "publish"} onClick={() => void publish()}>
                <Send size={17} /> Опубликовать
              </Button>
            ) : null}
          </div>
        }
      />
      {message && <Toast message={message} />}
      {error && <Toast message={error} type="error" />}

      <form className="editor-grid" onSubmit={save}>
        <Card>
          <div className="form-grid">
            <FormField label="Название">
              <input required minLength={3} value={form.title} onChange={(event) => updateField("title", event.target.value)} />
            </FormField>
            <FormField label="Цена одного билета, USDT">
              <input required disabled={prizesLocked} inputMode="decimal" value={form.ticket_price} onChange={(event) => updateField("ticket_price", event.target.value)} />
            </FormField>
            <FormField label="Начало продаж">
              <input type="datetime-local" required disabled={prizesLocked} value={form.sales_start_at} onChange={(event) => updateField("sales_start_at", event.target.value)} />
            </FormField>
            <FormField label="Дедлайн продаж">
              <input type="datetime-local" required disabled={prizesLocked} value={form.sales_end_at} onChange={(event) => updateField("sales_end_at", event.target.value)} />
            </FormField>
            <FormField label="Дата и время результатов">
              <input type="datetime-local" required disabled={prizesLocked} value={form.draw_at} onChange={(event) => updateField("draw_at", event.target.value)} />
            </FormField>
            <FormField label="Максимум билетов на пользователя">
              <input type="number" min={1} max={10000} required disabled={prizesLocked} value={form.max_tickets_per_user} onChange={(event) => updateField("max_tickets_per_user", Number(event.target.value))} />
            </FormField>
            <FormField label="Общий лимит билетов" hint="Оставьте пустым, если лимита нет.">
              <input type="number" min={1} disabled={prizesLocked} value={form.max_tickets_total ?? ""} onChange={(event) => updateField("max_tickets_total", event.target.value ? Number(event.target.value) : null)} />
            </FormField>
            <FormField label="Telegram менеджера" hint="Например, @automotive_manager или полная ссылка.">
              <input value={form.manager_telegram ?? ""} onChange={(event) => updateField("manager_telegram", event.target.value || null)} />
            </FormField>
          </div>
          <FormField label="Краткое и полное описание">
            <textarea required minLength={10} rows={7} value={form.description} onChange={(event) => updateField("description", event.target.value)} />
          </FormField>
          <FormField label="URL обложки">
            <input type="url" value={form.cover_image_url ?? ""} onChange={(event) => updateField("cover_image_url", event.target.value || null)} />
          </FormField>
          <FormField label="Правила лотереи">
            <textarea required minLength={20} rows={12} disabled={prizesLocked} value={form.rules_text} onChange={(event) => updateField("rules_text", event.target.value)} />
            <span className="field-hint">
              До публикации обязательно укажите метод определения победителей, требования к участникам, срок получения приза, налоги и доставку, основания дисквалификации, порядок замены победителя, отмены и возврата. После первой продажи правила блокируются.
            </span>
          </FormField>
          <FormField label="Версия правил">
            <input required disabled={prizesLocked} value={form.rules_version} onChange={(event) => updateField("rules_version", event.target.value)} />
          </FormField>
          {prizesLocked ? (
            <div className="notice">
              После продажи первого билета цена, даты, лимиты и версия правил
              фиксируются. Название, описание, обложку и контакт менеджера можно
              продолжать обновлять.
            </div>
          ) : null}
          <div className="form-actions">
            <Button type="submit" loading={saving}><Save size={17} /> {isNew ? "Создать" : "Сохранить"}</Button>
          </div>
        </Card>
        <aside>
          <Card className="preview-card">
            {form.cover_image_url ? <img src={form.cover_image_url} alt="Предпросмотр обложки" /> : null}
            <StatusBadge value={lottery?.status || "draft"} />
            <h2>{form.title || "Название лотереи"}</h2>
            <p>{form.description || "Описание появится здесь."}</p>
            <dl>
              <div><dt>Билет</dt><dd>{form.ticket_price} USDT</dd></div>
              <div><dt>Дедлайн</dt><dd>{form.sales_end_at ? formatDateTime(isoDate(form.sales_end_at)) : "—"}</dd></div>
              <div><dt>Результаты</dt><dd>{form.draw_at ? formatDateTime(isoDate(form.draw_at)) : "—"}</dd></div>
              <div><dt>Продано</dt><dd>{lottery?.tickets_sold ?? 0}</dd></div>
            </dl>
          </Card>
        </aside>
      </form>

      {!isNew && lottery && id ? (
        <div className="lottery-admin-sections">
          <Card>
            <div className="card-heading-row">
              <div><h2>Призы</h2><p>Количество определяет число призовых мест этого типа.</p></div>
            </div>
            {lottery.prizes.length ? (
              <div className="admin-prize-grid">
                {lottery.prizes.map((prize) => (
                  <article className="admin-prize-card" key={prize.id}>
                    {prize.image_url ? <img src={prize.image_url} alt="" /> : <div className="admin-prize-placeholder"><Gift /></div>}
                    <div>
                      <StatusBadge value={prize.prize_type} />
                      <h3>{prize.title}</h3>
                      <p>{prize.description}</p>
                      <strong>{prize.quantity} призовых мест</strong>
                      {prize.amount ? <span>{formatMoney(prize.amount)} {prize.asset}</span> : null}
                      {!prizesLocked ? (
                        <div className="row-actions">
                          <Button variant="ghost" onClick={() => beginPrizeEdit(prize)}>Редактировать</Button>
                          <Button variant="danger" loading={actionLoading === `delete-prize-${prize.id}`} onClick={() => void removePrize(prize)}><Trash2 size={16} /> Удалить</Button>
                        </div>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            ) : <EmptyState title="Призы не добавлены" description="Добавьте хотя бы один приз перед публикацией." />}

            {prizesLocked ? (
              <div className="notice">Состав и количество призов зафиксированы после первой покупки билета.</div>
            ) : (
            <form id="lottery-prize-form" className="nested-form" onSubmit={savePrize}>
              <div className="nested-form-heading">
                <h3>{editingPrizeId ? "Редактирование приза" : "Новый приз"}</h3>
                {editingPrizeId ? <Button type="button" variant="ghost" onClick={resetPrizeForm}><XCircle size={16} /> Отмена</Button> : null}
              </div>
              <div className="form-grid">
                <FormField label="Название приза"><input required minLength={2} value={prizeForm.title} onChange={(event) => setPrizeForm((current) => ({ ...current, title: event.target.value }))} /></FormField>
                <FormField label="Тип приза">
                  <select value={prizeForm.prize_type} onChange={(event) => setPrizeForm((current) => ({ ...current, prize_type: event.target.value as LotteryPrizeType, amount: event.target.value === "balance" ? current.amount || "10.000000" : null }))}>
                    <option value="balance">Денежный — на баланс</option>
                    <option value="physical">Неденежный — через менеджера</option>
                  </select>
                </FormField>
                {prizeForm.prize_type === "balance" ? <FormField label="Сумма, USDT"><input required value={prizeForm.amount ?? ""} onChange={(event) => setPrizeForm((current) => ({ ...current, amount: event.target.value }))} /></FormField> : <FormField label="Telegram менеджера"><input value={prizeForm.manager_telegram ?? ""} onChange={(event) => setPrizeForm((current) => ({ ...current, manager_telegram: event.target.value || null }))} /></FormField>}
                <FormField label="Количество"><input type="number" min={1} max={1000} required value={prizeForm.quantity} onChange={(event) => setPrizeForm((current) => ({ ...current, quantity: Number(event.target.value) }))} /></FormField>
                <FormField label="Порядок"><input type="number" min={0} value={prizeForm.sort_order} onChange={(event) => setPrizeForm((current) => ({ ...current, sort_order: Number(event.target.value) }))} /></FormField>
                <FormField label="URL изображения"><input type="url" value={prizeForm.image_url ?? ""} onChange={(event) => setPrizeForm((current) => ({ ...current, image_url: event.target.value || null }))} /></FormField>
              </div>
              <FormField label="Описание"><textarea rows={4} value={prizeForm.description} onChange={(event) => setPrizeForm((current) => ({ ...current, description: event.target.value }))} /></FormField>
              <Button type="submit" loading={actionLoading === "prize"}><Plus size={16} /> {editingPrizeId ? "Сохранить приз" : "Добавить приз"}</Button>
            </form>
            )}
          </Card>

          <Card>
            <div className="card-heading-row">
              <div><h2>Розыгрыш и победители</h2><p>Сначала выберите кандидатов, затем отдельно подтвердите выдачу каждого приза.</p></div>
              <div className="page-actions">
                <Button variant="secondary" loading={actionLoading === "draw"} onClick={() => void drawRandom()}><Dice5 size={17} /> Случайный выбор</Button>
                {lottery.pending_winners_count > 0 ? <Button loading={actionLoading === "confirm-all"} onClick={() => void confirmAll()}><CheckCircle2 size={17} /> Подтвердить всех</Button> : null}
              </div>
            </div>

            <form className="ticket-search-form" onSubmit={(event) => void searchTickets(event)}>
              <FormField label="Найти билет" hint="По коду билета или email пользователя. Поиск охватывает все проданные билеты.">
                <input
                  value={ticketSearch}
                  placeholder="Например, ABCD-1234 или user@example.com"
                  onChange={(event) => setTicketSearch(event.target.value)}
                />
              </FormField>
              <Button type="submit" variant="secondary" loading={ticketSearchLoading}>
                <Search size={17} /> Найти
              </Button>
            </form>

            <form className="manual-winner-form" onSubmit={manualWinner}>
              <FormField label="Призовое место">
                <select required value={manualPrizeId} onChange={(event) => setManualPrizeId(event.target.value)}>
                  <option value="">Выберите приз</option>
                  {remainingPrizes.map((prize) => <option key={prize.id} value={prize.id}>{prize.title}</option>)}
                </select>
              </FormField>
              <FormField label="Билет пользователя">
                <select required value={manualTicketId} onChange={(event) => setManualTicketId(event.target.value)}>
                  <option value="">Выберите билет</option>
                  {availableTickets.map((ticket) => <option key={ticket.id} value={ticket.id}>{ticket.ticket_code} — {ticket.user_email}</option>)}
                </select>
              </FormField>
              <Button type="submit" loading={actionLoading === "manual"}><UserCheck size={17} /> Выбрать вручную</Button>
            </form>

            <FormField label="Комментарий при подтверждении" hint="Необязательно. Сохранится у победителя и в аудите.">
              <textarea rows={2} value={confirmationNote} onChange={(event) => setConfirmationNote(event.target.value)} />
            </FormField>

            {lottery.admin_winners.length ? (
              <DataTable label="Победители лотереи">
                <thead><tr><th>Приз</th><th>Победитель</th><th>Билет</th><th>Способ</th><th>Статус</th><th>Выбран</th><th /></tr></thead>
                <tbody>
                  {lottery.admin_winners.map((winner) => (
                    <tr key={winner.id}>
                      <td><strong>{winner.prize_title}</strong><small>{winner.prize_amount ? `${formatMoney(winner.prize_amount)} USDT` : label(winner.prize_type)}</small></td>
                      <td>{winner.user_email}</td>
                      <td><code>{winner.ticket_code}</code></td>
                      <td>{label(winner.selection_method)}</td>
                      <td><StatusBadge value={winner.status} /></td>
                      <td>{formatDateTime(winner.selected_at)}</td>
                      <td className="row-actions">
                        {winner.status === "pending" ? <>
                          <Button loading={actionLoading === `confirm-${winner.id}`} onClick={() => void confirmWinner(winner.id)}><Trophy size={15} /> Подтвердить</Button>
                          <Button variant="danger" loading={actionLoading === `remove-${winner.id}`} onClick={() => void removeWinner(winner.id)}><Trash2 size={15} /> Отменить</Button>
                        </> : winner.confirmed_at ? <span>{formatDateTime(winner.confirmed_at)}</span> : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
            ) : <EmptyState title="Победители ещё не выбраны" description="После дедлайна используйте случайный или ручной выбор." />}
          </Card>

          <Card>
            <div className="card-heading-row"><div><h2>Проданные билеты</h2><p>Показаны до 100 билетов. Используйте поиск, чтобы найти нужный билет среди всех продаж.</p></div><span className="metric-inline"><Ticket size={18} /> {lottery.tickets_sold}</span></div>
            {tickets.length ? (
              <DataTable label="Билеты лотереи">
                <thead><tr><th>Код</th><th>Пользователь</th><th>Куплен</th><th>Статус</th><th>Победитель</th></tr></thead>
                <tbody>{tickets.map((ticket) => <tr key={ticket.id}><td><code>{ticket.ticket_code}</code></td><td>{ticket.user_email}</td><td>{formatDateTime(ticket.purchased_at)}</td><td><StatusBadge value={ticket.status} /></td><td>{ticket.is_winner ? "Да" : "Нет"}</td></tr>)}</tbody>
              </DataTable>
            ) : <EmptyState title="Билетов пока нет" description="Список заполнится после первых покупок." />}
          </Card>
        </div>
      ) : null}
    </>
  );
}
