import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { listPlans } from "../api/plans";
import type { Plan } from "../api/types";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PlanCard } from "../components/PlanCard";
import { compareMoney } from "../utils/money";

export function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("default");
  useEffect(() => {
    listPlans(1, 100)
      .then((data) => setPlans(data.items))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);
  const filtered = useMemo(() => {
    const result = plans.filter((plan) =>
      `${plan.title} ${plan.short_description}`
        .toLowerCase()
        .includes(query.toLowerCase()),
    );
    if (sort === "price-asc")
      result.sort((a, b) => compareMoney(a.price, b.price));
    if (sort === "price-desc")
      result.sort((a, b) => compareMoney(b.price, a.price));
    if (sort === "title")
      result.sort((a, b) => a.title.localeCompare(b.title, "ru"));
    return result;
  }, [plans, query, sort]);
  return (
    <section className="section page-hero">
      <div className="container">
        <div className="section-heading">
          <p className="eyebrow">Программа подписок</p>
          <h1>Условия для клиентов автомобильной компании</h1>
          <p>
            Стоимость, срок действия и график вознаграждений загружаются из системы управления программами.
            Служебные категории `game/application` намеренно не показываются на
            автомобильном сайте.
          </p>
        </div>
        <div className="catalog-tools">
          <label className="search-field">
            <Search size={18} />
            <span className="sr-only">Поиск</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Найти программу"
            />
          </label>
          <label>
            <span>Сортировка</span>
            <select value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="default">По умолчанию</option>
              <option value="price-asc">Сначала дешевле</option>
              <option value="price-desc">Сначала дороже</option>
              <option value="title">По названию</option>
            </select>
          </label>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="notice danger">{error}</div>
        ) : filtered.length ? (
          <div className="plans-grid">
            {filtered.map((plan) => (
              <PlanCard key={plan.id} plan={plan} />
            ))}
          </div>
        ) : (
          <EmptyState
            title="Ничего не найдено"
            text="Измените поисковый запрос или дождитесь публикации новых программ."
          />
        )}
      </div>
    </section>
  );
}
