import { content } from "../config/content";
export function FaqPage() {
  return (
    <section className="section page-hero">
      <div className="container narrow">
        <p className="eyebrow">FAQ</p>
        <h1>Частые вопросы</h1>
        <div className="faq-list">
          {content.faq.map(([question, answer]) => (
            <details key={question}>
              <summary>{question}</summary>
              <p>{answer}</p>
            </details>
          ))}
          <details>
            <summary>Как рассчитывается вознаграждение?</summary>
            <p>
              Сумма, частота и длительность начислений заранее указаны в
              условиях каждой клиентской программы.
            </p>
          </details>
          <details>
            <summary>Можно ли участвовать сразу в нескольких программах?</summary>
            <p>
              Доступные варианты участия определяются актуальными условиями,
              опубликованными в каталоге программ.
            </p>
          </details>
        </div>
      </div>
    </section>
  );
}
