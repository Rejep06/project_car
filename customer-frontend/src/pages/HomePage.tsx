import {
  ArrowRight,
  BarChart3,
  Car,
  CheckCircle2,
  Headphones,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPlans } from "../api/plans";
import { listPosts } from "../api/posts";
import type { Plan, Post } from "../api/types";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PlanCard } from "../components/PlanCard";
import { content } from "../config/content";
import { formatDateOnly } from "../utils/date";

export function HomePage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.allSettled([listPlans(1, 6), listPosts(1, 3)]).then(
      ([planResult, postResult]) => {
        if (planResult.status === "fulfilled") setPlans(planResult.value.items);
        else setError("Не удалось загрузить варианты программы.");
        if (postResult.status === "fulfilled") setPosts(postResult.value.items);
        setLoading(false);
      },
    );
  }, []);
  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">
              Автомобильная компания · клиентская программа
            </p>
            <h1>{content.heroTitle}</h1>
            <p>{content.heroText}</p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/plans">
                Посмотреть программы <ArrowRight size={18} />
              </Link>
              <Link className="button button-secondary" to="/how-it-works">
                Как это работает
              </Link>
            </div>
            <div className="hero-trust">
              <span>
                <ShieldCheck /> Фиксированные условия
              </span>
              <span>
                <BarChart3 /> Прозрачный график
              </span>
            </div>
          </div>
          <div
            className="hero-visual"
            aria-label="Демонстрационная карточка автомобильной программы"
          >
            <div className="car-stage">
              <Car size={112} strokeWidth={1.2} />
              <span className="road-line" />
            </div>
            <Card className="hero-program-card">
              <p>Программа программы</p>
              <strong>Условия программы публикуются компанией</strong>
              <span>Стоимость · срок · вознаграждение</span>
            </Card>
          </div>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">О компании</p>
            <h2>Автомобили и современный клиентский сервис</h2>
            <p>{content.aboutText}</p>
          </div>
          <div className="stats-grid">
            <Card>
              <strong>{content.sinceYear}</strong>
              <span>работаем с года</span>
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
      <section className="section dark-section">
        <div className="container">
          <div className="section-heading light">
            <p className="eyebrow">Как работает программа</p>
            <h2>Четыре понятных шага</h2>
          </div>
          <div className="steps-grid">
            {[
              "Создайте аккаунт",
              "Пополните баланс USDT",
              "Выберите программу программы",
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
      <section className="section">
        <div className="container">
          <div className="section-heading row-heading">
            <div>
              <p className="eyebrow">Варианты программы</p>
              <h2>Выберите условия программы</h2>
            </div>
            <Link className="text-link" to="/plans">
              Все программы →
            </Link>
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <div className="notice danger">{error}</div>
          ) : plans.length ? (
            <div className="plans-grid">
              {plans.map((plan) => (
                <PlanCard key={plan.id} plan={plan} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Активных программ пока нет"
              text="Администратор сможет добавить их через отдельную панель."
            />
          )}
        </div>
      </section>
      <section className="section subtle-section">
        <div className="container">
          <div className="section-heading">
            <p className="eyebrow">Прозрачность условий</p>
            <h2>Все операции доступны в личном кабинете</h2>
          </div>
          <div className="feature-grid">
            {[
              [CheckCircle2, "Условия фиксируются при покупке"],
              [BarChart3, "Понятный график начислений"],
              [WalletCards, "Доступный и заблокированный баланс"],
              [Headphones, "Поддержка по TxID и вложениям"],
            ].map(([Icon, title]) => {
              const FeatureIcon = Icon as typeof CheckCircle2;
              return (
                <Card key={title as string}>
                  <FeatureIcon />
                  <h3>{title as string}</h3>
                  <p>Фактические значения и статусы приходят из FastAPI.</p>
                </Card>
              );
            })}
          </div>
          <div className="legal-note">{content.legalClarification}</div>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <div className="section-heading row-heading">
            <div>
              <p className="eyebrow">Новости компании</p>
              <h2>Последние публикации</h2>
            </div>
            <Link className="text-link" to="/news">
              Все новости →
            </Link>
          </div>
          {posts.length ? (
            <div className="news-grid">
              {posts.map((post) => (
                <Card key={post.id} className="news-card">
                  <p className="small muted">
                    {formatDateOnly(post.published_at)}
                  </p>
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
              text="Здесь появятся новости автомобильной компании и программы подписок."
            />
          )}
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
          <Link className="button button-secondary" to="/faq">
            Все вопросы
          </Link>
        </div>
      </section>
    </>
  );
}
