import { CalendarDays, Ticket, Trophy } from "lucide-react";
import { Link } from "react-router-dom";
import type { LotterySummary } from "../api/types";
import { formatDate } from "../utils/date";
import { Card } from "./Card";
import { MoneyValue } from "./MoneyValue";

const statusLabels: Record<LotterySummary["status"], string> = {
  draft: "Черновик",
  published: "Продажа билетов",
  awaiting_confirmation: "Победители определяются",
  completed: "Завершена",
  cancelled: "Отменена",
};

interface LotteryCardProps {
  lottery: LotterySummary;
  headingLevel?: "h2" | "h3";
  imageLoading?: "eager" | "lazy";
}

export function LotteryCard({
  lottery,
  headingLevel = "h2",
  imageLoading = "lazy",
}: LotteryCardProps) {
  const Heading = headingLevel;

  return (
    <Card className="lottery-card">
      <img
        src={lottery.cover_image_url || "/assets/program-car-photo.jpg"}
        alt={`Лотерея «${lottery.title}»`}
        loading={imageLoading}
      />
      <div className="lottery-card-body">
        <span className={`lottery-status lottery-status-${lottery.status}`}>
          {statusLabels[lottery.status]}
        </span>
        <Heading>{lottery.title}</Heading>
        <p>{lottery.description}</p>
        <dl className="lottery-facts">
          <div>
            <Ticket size={17} />
            <dt>Билет</dt>
            <dd><MoneyValue value={lottery.ticket_price} /></dd>
          </div>
          <div>
            <CalendarDays size={17} />
            <dt>Дедлайн</dt>
            <dd>{formatDate(lottery.sales_end_at)}</dd>
          </div>
          <div>
            <Trophy size={17} />
            <dt>Продано</dt>
            <dd>{lottery.tickets_sold}</dd>
          </div>
        </dl>
        <Link className="button button-primary" to={`/lotteries/${lottery.id}`}>
          Открыть лотерею
        </Link>
      </div>
    </Card>
  );
}
