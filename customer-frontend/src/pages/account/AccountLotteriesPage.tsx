import { Gift, Ticket, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMyLotteryTickets } from "../../api/lotteries";
import type { LotteryTicket } from "../../api/types";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { Pagination } from "../../components/Pagination";
import { formatDate } from "../../utils/date";

const pageSize = 20;

export function AccountLotteriesPage() {
  const [items, setItems] = useState<LotteryTicket[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    listMyLotteryTickets(page, pageSize)
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="account-page">
      <div className="page-title">
        <div><p className="eyebrow">Розыгрыши</p><h1>Мои билеты и призы</h1></div>
        <Link className="button button-primary" to="/lotteries">Все лотереи</Link>
      </div>
      {loading ? <LoadingSpinner /> : error ? <div className="notice danger">{error}</div> : items.length ? (
        <div className="ticket-list">
          {items.map((ticket) => (
            <Card key={ticket.id} className={ticket.winner_status === "confirmed" ? "ticket-card winner" : "ticket-card"}>
              <div className="ticket-code"><Ticket size={20} /><code>{ticket.ticket_code}</code></div>
              <h2>{ticket.lottery_title}</h2>
              <dl className="compact-dl">
                <div><dt>Куплен</dt><dd>{formatDate(ticket.purchased_at)}</dd></div>
                <div><dt>Дата результатов</dt><dd>{formatDate(ticket.draw_at)}</dd></div>
                <div><dt>Стоимость</dt><dd><MoneyValue value={ticket.price} /></dd></div>
              </dl>
              {ticket.prize_title && (
                <div className="winner-panel">
                  {ticket.prize_type === "balance" ? <Trophy /> : <Gift />}
                  <div>
                    <strong>Вы выиграли: {ticket.prize_title}</strong>
                    {ticket.prize_amount && <p><MoneyValue value={ticket.prize_amount} /></p>}
                    {ticket.claim_contact && <p>Менеджер: <a href={ticket.claim_contact.startsWith("http") ? ticket.claim_contact : `https://t.me/${ticket.claim_contact.replace(/^@/, "")}`} target="_blank" rel="noreferrer">{ticket.claim_contact}</a></p>}
                    {ticket.winner_status === "pending" && <p>Победа ожидает подтверждения администратора.</p>}
                  </div>
                </div>
              )}
              <Link to={`/lotteries/${ticket.lottery_id}`}>Открыть лотерею</Link>
            </Card>
          ))}
        </div>
      ) : <EmptyState title="Билетов пока нет" text="Выберите опубликованную лотерею и купите первый билет." />}
      <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
    </div>
  );
}
