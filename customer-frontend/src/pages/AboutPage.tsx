import { Card } from "../components/Card";
import { content } from "../config/content";
export function AboutPage() {
  return (
    <section className="section page-hero">
      <div className="container narrow">
        <p className="eyebrow">О компании</p>
        <h1>Автомобили, партнёрская сеть и цифровой сервис</h1>
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
        <h2>Клиентская программа</h2>
        <p>
          Компания помогает людям участвовать в специальных клиентских
          программах с понятными условиями. Каждая программа имеет своё название,
          описание, стоимость, срок действия и график вознаграждений.
          Программы обеспечиваются автомобилями компании. Подробные условия
          обеспечения публикуются отдельно.
        </p>
      </div>
    </section>
  );
}
