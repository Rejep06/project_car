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
            <summary>Есть ли гарантированный процент?</summary>
            <p>
              Нет. Система хранит фиксированную сумму одного вознаграждения и
              график начислений конкретной программы; это не банковский процент.
            </p>
          </details>
          <details>
            <summary>Как защищена повторная покупка?</summary>
            <p>
              Запрос покупки передаёт стабильный Idempotency-Key. Повторная
              отправка не должна списывать средства второй раз.
            </p>
          </details>
        </div>
      </div>
    </section>
  );
}
