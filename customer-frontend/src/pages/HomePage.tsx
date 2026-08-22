import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Headphones,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listLotteries } from "../api/lotteries";
import { listPlans } from "../api/plans";
import { listPosts } from "../api/posts";
import type { LotterySummary, Plan, Post } from "../api/types";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { LotteryCard } from "../components/LotteryCard";
import { PlanCard } from "../components/PlanCard";
import { heroCarPhotoUrl } from "../config/assets";
import { content } from "../config/content";
import { formatDateOnly } from "../utils/date";

function lotteryPriority(lottery: LotterySummary): number {
  if (lottery.sales_open) return 0;
  if (lottery.status === "published") return 1;
  if (lottery.status === "awaiting_confirmation") return 2;
  if (lottery.status === "completed") return 3;
  return 4;
}

function selectFeaturedLotteries(items: LotterySummary[]): LotterySummary[] {
  return [...items]
    .sort((left, right) => {
      const priorityDifference = lotteryPriority(left) - lotteryPriority(right);
      if (priorityDifference !== 0) return priorityDifference;

      const leftDate = new Date(left.sales_end_at).getTime();
      const rightDate = new Date(right.sales_end_at).getTime();
      if (lotteryPriority(left) >= 3) return rightDate - leftDate;
      return leftDate - rightDate;
    })
    .slice(0, 3);
}

export function HomePage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [lotteries, setLotteries] = useState<LotterySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [plansError, setPlansError] = useState("");
  const [postsError, setPostsError] = useState("");
  const [lotteriesError, setLotteriesError] = useState("");

  useEffect(() => {
    Promise.allSettled([
      listPlans(1, 6),
      listPosts(1, 3),
      listLotteries(1, 12),
    ]).then(([planResult, postResult, lotteryResult]) => {
      if (planResult.status === "fulfilled") {
        setPlans(planResult.value.items);
      } else {
        setPlansError("Не удалось загрузить программы.");
      }

      if (postResult.status === "fulfilled") {
        setPosts(postResult.value.items);
      } else {
        setPostsError("Не удалось загрузить публикации.");
      }

      if (lotteryResult.status === "fulfilled") {
        setLotteries(selectFeaturedLotteries(lotteryResult.value.items));
      } else {
        setLotteriesError("Не удалось загрузить лотереи.");
      }

      setLoading(false);
    });
  }, []);

  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Автомобильная компания · с 2023 года</p>
            <h1>{content.heroTitle}</h1>
            <p>{content.heroText}</p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/plans">
                Посмотреть программы <ArrowRight size={18} />
              </Link>
              <Link className="button button-secondary" to="/lotteries">
                Открыть лотереи
              </Link>
            </div>
            <div className="hero-trust">
              <span><ShieldCheck /> Понятные условия</span>
              <span><BarChart3 /> График вознаграждений</span>
            </div>
          </div>
          <div
            className="hero-visual"
            aria-label="Демонстрационная карточка автомобильной программы"
          >
            <img
              className="hero-car-photo"
              src={heroCarPhotoUrl}
              alt="Автомобиль в современном шоуруме"
            />
            <Card className="hero-program-card">
              <p>Клиентская программа</p>
              <strong>Три уровня на выбор</strong>
              <span>Старт · Стандарт · Премиум</span>
            </Card>
          </div>
        </div>
      </section>

      <section className="section home-lotteries">
        <div className="container">
          <div className="section-heading row-heading">
            <div>
              <p className="eyebrow">Розыгрыши Automotive Club</p>
              <h2>Актуальные лотереи</h2>
              <p>
                Изучите условия, сроки и призы. Подтверждённые результаты
                публикуются на странице каждой лотереи.
              </p>
            </div>
            <Link className="text-link" to="/lotteries">Все лотереи →</Link>
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : lotteriesError ? (
            <div className="notice danger">{lotteriesError}</div>
          ) : lotteries.length ? (
            <div className="lottery-grid">
              {lotteries.map((lottery, index) => (
                <LotteryCard
                  key={lottery.id}
                  lottery={lottery}
                  headingLevel="h3"
                  imageLoading={index === 0 ? "eager" : "lazy"}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Лотерей пока нет"
              text="После публикации новые розыгрыши появятся прямо на главной странице."
            />
          )}
        </div>
      </section>

      <section className="section subtle-section home-publications">
        <div className="container">
          <div className="section-heading row-heading">
            <div>
              <p className="eyebrow">Главное о компании</p>
              <h2>Публикации и новости</h2>
              <p>
                Новости компании, развитие автомобильного направления,
                обновления программ и полезные материалы для клиентов.
              </p>
            </div>
            <Link className="text-link" to="/news">Все публикации →</Link>
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : postsError ? (
            <div className="notice danger">{postsError}</div>
          ) : posts.length ? (
            <div className="news-grid">
              {posts.map((post) => (
                <Card key={post.id} className="news-card">
                  <p className="small muted">{formatDateOnly(post.published_at)}</p>
                  <h3>{post.title}</h3>
                  <p>{post.excerpt}</p>
                  <Link to={`/news/${post.slug}`}>
                    Читать <ArrowRight size={16} />
                  </Link>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Публикаций пока нет"
              text="Здесь будут появляться новости и материалы компании."
            />
          )}
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">О компании</p>
            <h2>Помогаем людям получать дополнительный заработок</h2>
            <p>{content.aboutText}</p>
          </div>
          <div className="stats-grid">
            <Card>
              <strong>{content.sinceYear}</strong>
              <span>год начала работы</span>
            </Card>
            <Card>
              <strong>{content.carsPerMonth}</strong>
              <span>автомобилей в среднем в месяц</span>
            </Card>
            <Card>
              <strong>{content.partners}</strong>
              <span>партнёров</span>
            </Card>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading row-heading">
            <div>
              <p className="eyebrow">Три уровня</p>
              <h2>Выберите свою программу</h2>
            </div>
            <Link className="text-link" to="/plans">Все программы →</Link>
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : plansError ? (
            <div className="notice danger">{plansError}</div>
          ) : plans.length ? (
            <div className="plans-grid">
              {plans.map((plan) => <PlanCard key={plan.id} plan={plan} />)}
            </div>
          ) : (
            <EmptyState
              title="Программы временно недоступны"
              text="Актуальные условия появятся в этом разделе."
            />
          )}
        </div>
      </section>

      <section className="section dark-section">
        <div className="container">
          <div className="section-heading light">
            <p className="eyebrow">Как начать</p>
            <h2>Четыре понятных шага</h2>
          </div>
          <div className="steps-grid">
            {[
              "Создайте аккаунт",
              "Пополните баланс USDT",
              "Выберите клиентскую программу",
              "Получайте вознаграждения по графику",
            ].map((step, index) => (
              <div className="step" key={step}>
                <span>{index + 1}</span>
                <h3>{step}</h3>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section subtle-section">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">Удобный личный кабинет</p>
            <h2>Все важное всегда под рукой</h2>
          </div>
          <div className="feature-grid">
            {[
              [CheckCircle2, "Условия программы после активации"],
              [BarChart3, "Календарь начислений"],
              [WalletCards, "Баланс и история операций"],
              [Headphones, "Поддержка с вложениями"],
            ].map(([Icon, title]) => {
              const FeatureIcon = Icon as typeof CheckCircle2;
              return (
                <Card key={title as string}>
                  <FeatureIcon />
                  <h3>{title as string}</h3>
                  <p>Информация доступна в удобном формате на компьютере и телефоне.</p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      <section className="section faq-preview">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">Вопросы</p>
            <h2>Основное перед началом</h2>
          </div>
          <div className="faq-list">
            {content.faq.slice(0, 3).map(([question, answer]) => (
              <details key={question}>
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
          <Link className="button button-secondary" to="/faq">Все вопросы</Link>
        </div>
      </section>
    </>
  );
}
