import { ArrowRight, CalendarDays, Coins } from "lucide-react";
import { Link } from "react-router-dom";
import type { Plan } from "../api/types";
import {
  durationLabels,
  estimateRewardCount,
  estimateRewardTotal,
  frequencyLabels,
} from "../utils/rewards";
import { planTierLabels } from "../utils/programs";
import { Card } from "./Card";
import { MoneyValue } from "./MoneyValue";
import { ProgramImage } from "./ProgramImage";

export function PlanCard({ plan }: { plan: Plan }) {
  const count = estimateRewardCount(plan);
  return (
    <Card className="plan-card">
      <div className="plan-card-image">
        <ProgramImage
          src={plan.image_url}
          alt={`Автомобиль для программы «${plan.title}»`}
        />
      </div>
      <div className="plan-card-body">
        <p className={`program-tier program-tier-${plan.tier}`}>{planTierLabels[plan.tier]}</p>
        <h3>{plan.title}</h3>
        <p>
          {plan.short_description ||
            "Условия программы доступны на странице подробностей."}
        </p>
        <dl className="plan-facts">
          <div>
            <dt>Стоимость</dt>
            <dd>
              <MoneyValue value={plan.price} />
            </dd>
          </div>
          <div>
            <dt>
              <CalendarDays size={16} /> Срок
            </dt>
            <dd>
              {plan.access_duration_value}{" "}
              {durationLabels[plan.access_duration_unit]}
            </dd>
          </div>
          <div>
            <dt>
              <Coins size={16} /> Вознаграждение
            </dt>
            <dd>
              <MoneyValue value={plan.reward_amount} />{" "}
              {frequencyLabels[plan.reward_frequency]}
            </dd>
          </div>
          <div>
            <dt>Предусмотренная сумма</dt>
            <dd>
              ориентировочно <MoneyValue value={estimateRewardTotal(plan)} />
            </dd>
          </div>
        </dl>
        <p className="small muted">
          Ориентировочное количество начислений: {count}. Точный график
          фиксируется при активации программы.
        </p>
        <Link className="button button-primary" to={`/plans/${plan.id}`}>
          Подробнее <ArrowRight size={17} />
        </Link>
      </div>
    </Card>
  );
}
