import { CarFront, HandCoins, ShieldCheck } from "lucide-react";
import { Card } from "../components/Card";
import { content } from "../config/content";

export function AboutPage() {
  return (
    <section className="section page-hero">
      <div className="container narrow">
        <p className="eyebrow">О компании</p>
        <h1>Развиваем автомобильное направление с 2023 года</h1>
        <p className="lead">{content.aboutText}</p>
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

        <div className="about-values-grid">
          <Card>
            <HandCoins />
            <h2>Помогаем зарабатывать</h2>
            <p>
              Наша цель — дать людям понятный способ получать дополнительный
              заработок через клиентские программы с заранее опубликованными
              условиями.
            </p>
          </Card>
          <Card>
            <ShieldCheck />
            <h2>Автомобильное обеспечение</h2>
            <p>
              Участие в клиентских программах обеспечивается автомобилями
              компании. Подробности и новости об автомобильном направлении
              публикуются на сайте.
            </p>
          </Card>
          <Card>
            <CarFront />
            <h2>Три программы</h2>
            <p>
              Клиент может выбрать стартовый, стандартный или премиальный
              уровень. У каждой программы есть собственные название, описание,
              стоимость, срок и график вознаграждений.
            </p>
          </Card>
        </div>
      </div>
    </section>
  );
}
