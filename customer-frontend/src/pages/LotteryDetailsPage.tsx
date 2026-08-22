import { CalendarDays, Ticket, Trophy } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  buyLotteryTickets,
  getLottery,
  getMyLotteryTickets,
} from "../api/lotteries";
import type { LotteryDetail, LotteryTicket } from "../api/types";
import { getWallet } from "../api/wallet";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { MoneyValue } from "../components/MoneyValue";
import { showToast } from "../components/Toast";
import { formatDate } from "../utils/date";
import { compareMoney, multiplyMoney } from "../utils/money";

export function LotteryDetailsPage() {
  const { id = "" } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [lottery, setLottery] = useState<LotteryDetail | null>(null);
  const [myTickets, setMyTickets] = useState<LotteryTicket[]>([]);
  const [balance, setBalance] = useState("0.000000");
  const [quantity, setQuantity] = useState(1);
  const [rulesAccepted, setRulesAccepted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);
  const [error, setError] = useState("");
  const idempotencyKey = useRef(crypto.randomUUID());

  async function load() {
    const detail = await getLottery(id);
    setLottery(detail);
    if (user) {
      const [wallet, tickets] = await Promise.all([
        getWallet(),
        getMyLotteryTickets(id),
      ]);
      setBalance(wallet.available_balance);
      setMyTickets(tickets);
    }
  }

  useEffect(() => {
    setLoading(true);
    load()
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, user]);

  const total = useMemo(
    () => multiplyMoney(lottery?.ticket_price || "0.000000", quantity),
    [lottery?.ticket_price, quantity],
  );

  async function buy(event: FormEvent) {
    event.preventDefault();
    if (!user) {
      navigate("/login", { state: { from: location.pathname } });
      return;
    }
    if (!rulesAccepted) {
      showToast("Подтвердите согласие с правилами лотереи", "error");
      return;
    }
    setBuying(true);
    try {
      await buyLotteryTickets(id, quantity, idempotencyKey.current);
      idempotencyKey.current = crypto.randomUUID();
      showToast("Билеты успешно куплены", "success");
      setRulesAccepted(false);
      await load();
    } catch (reason) {
      showToast(reason instanceof Error ? reason.message : "Не удалось купить билет", "error");
    } finally {
      setBuying(false);
    }
  }

  if (loading) return <div className="page-center"><LoadingSpinner /></div>;
  if (error || !lottery) {
    return <section className="section"><div className="container notice danger">{error || "Лотерея не найдена"}</div></section>;
  }

  const enough = compareMoney(balance, total) >= 0;
  const remainingForUser = Math.max(0, lottery.max_tickets_per_user - myTickets.length);
  return (
    <section className="section page-hero">
      <div className="container lottery-detail-grid">
        <div>
          <img
            className="lottery-cover"
            src={lottery.cover_image_url || "/assets/program-car-photo.jpg"}
            alt={`Обложка лотереи «${lottery.title}»`}
          />
          <p className="eyebrow">Лотерея Automotive Club</p>
          <h1>{lottery.title}</h1>
          <p className="lead">{lottery.description}</p>

          <div className="lottery-highlight-grid">
            <Card><Ticket /><span>Цена билета</span><strong><MoneyValue value={lottery.ticket_price} /></strong></Card>
            <Card><CalendarDays /><span>Продажи до</span><strong>{formatDate(lottery.sales_end_at)}</strong></Card>
            <Card><Trophy /><span>Результаты</span><strong>{formatDate(lottery.draw_at)}</strong></Card>
          </div>

          <h2>Призы</h2>
          <div className="prize-grid">
            {lottery.prizes.map((prize) => (
              <Card key={prize.id} className="prize-card">
                {prize.image_url && <img src={prize.image_url} alt="" />}
                <span>{prize.quantity} шт.</span>
                <h3>{prize.title}</h3>
                <p>{prize.description}</p>
                {prize.amount && <MoneyValue value={prize.amount} />}
              </Card>
            ))}
          </div>

          <Card className="lottery-rules">
            <h2>Правила лотереи</h2>
            {lottery.rules_text.split("\n").filter(Boolean).map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
            <p className="small muted">Версия правил: {lottery.rules_version}</p>
          </Card>

          {lottery.winners.length > 0 && (
            <Card>
              <h2>Подтверждённые победители</h2>
              <div className="winner-list">
                {lottery.winners.map((winner) => (
                  <div key={winner.id}>
                    <Trophy size={18} />
                    <span>{winner.prize_title}</span>
                    <strong>{winner.ticket_code}</strong>
                    <span>{winner.winner_email_masked}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        <aside>
          <Card className="purchase-card sticky-card">
            <h2>Купить билет</h2>
            {lottery.sales_open && remainingForUser > 0 ? (
              <form className="form-stack" onSubmit={buy}>
                <label>
                  Количество
                  <input
                    type="number"
                    min={1}
                    max={Math.min(100, remainingForUser)}
                    value={Math.min(quantity, Math.min(100, remainingForUser))}
                    onChange={(event) => {
                      const limit = Math.min(100, remainingForUser);
                      setQuantity(Math.min(limit, Math.max(1, Number(event.target.value) || 1)));
                    }}
                  />
                </label>
                <dl>
                  <div><dt>Итого</dt><dd><MoneyValue value={total} /></dd></div>
                  {user && <div><dt>Ваш баланс</dt><dd><MoneyValue value={balance} /></dd></div>}
                </dl>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    required
                    checked={rulesAccepted}
                    onChange={(event) => setRulesAccepted(event.target.checked)}
                  />
                  <span>
                    Я ознакомился и принимаю правила этой лотереи версии {lottery.rules_version}, стоимость билета, дедлайн, способ определения победителей и порядок получения призов.
                  </span>
                </label>
                <Button type="submit" loading={buying} disabled={Boolean(user) && !enough}>
                  {user ? enough ? "Купить билеты" : "Недостаточно средств" : "Войти и купить"}
                </Button>
                {user && !enough && <Link to="/account/deposits">Пополнить баланс</Link>}
              </form>
            ) : remainingForUser === 0 ? (
              <div className="notice warning">Вы уже купили максимально доступное количество билетов для этой лотереи.</div>
            ) : (
              <div className="notice">Продажа билетов завершена или ещё не началась.</div>
            )}
            {myTickets.length > 0 && (
              <div className="my-ticket-preview">
                <h3>Ваши билеты: {myTickets.length}</h3>
                {myTickets.slice(0, 6).map((ticket) => <code key={ticket.id}>{ticket.ticket_code}</code>)}
                <Link to="/account/lotteries">Все мои билеты</Link>
              </div>
            )}
          </Card>
        </aside>
      </div>
    </section>
  );
}
