import { useEffect, useState } from "react";
import { listLotteries } from "../api/lotteries";
import type { LotterySummary } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { LotteryCard } from "../components/LotteryCard";

export function LotteriesPage() {
  const [items, setItems] = useState<LotterySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listLotteries(1, 50)
      .then((data) => setItems(data.items))
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="section page-hero">
      <div className="container">
        <div className="section-heading">
          <p className="eyebrow">Розыгрыши Automotive Club</p>
          <h1>Лотереи и призы</h1>
          <p>
            Выберите лотерею, изучите правила и купите билет до указанного
            дедлайна. Результаты и подтверждённые победители публикуются здесь.
          </p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="notice danger">{error}</div>
        ) : items.length ? (
          <div className="lottery-grid">
            {items.map((lottery) => (
              <LotteryCard key={lottery.id} lottery={lottery} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="Активных лотерей пока нет"
            text="Новые розыгрыши появятся на этой странице после публикации."
          />
        )}
      </div>
    </section>
  );
}
