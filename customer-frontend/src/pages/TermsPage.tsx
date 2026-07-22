import { content } from "../config/content";
export function TermsPage() {
  return (
    <section className="section page-hero">
      <div className="container narrow article-content">
        <h1>Условия использования</h1>
        <p>
          Этот демонстрационный документ необходимо заменить юридически
          проверенной редакцией до production-запуска.
        </p>
        <h2>Программа программы</h2>
        <p>
          Клиент приобретает подписку на опубликованных условиях. Цена, срок
          доступа, размер и частота вознаграждений фиксируются системой при
          покупке.
        </p>
        <h2>Внутренний баланс</h2>
        <p>
          Баланс является учётной записью в PostgreSQL. Реальные USDT находятся
          на аккаунте компании.
        </p>
        <div className="legal-note">{content.legalClarification}</div>
      </div>
    </section>
  );
}
