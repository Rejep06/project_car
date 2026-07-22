import { Link } from "react-router-dom";
export function HowItWorksPage() {
  const steps = [
    [
      "1",
      "Создайте аккаунт",
      "Регистрация создаёт профиль и внутренний кошелёк USDT.",
    ],
    [
      "2",
      "Создайте заявку на пополнение",
      "Система выдаст общий адрес TRON и уникальную точную сумму.",
    ],
    [
      "3",
      "Купите подписку",
      "Стоимость списывается с доступного внутреннего баланса.",
    ],
    [
      "4",
      "Следите за графиком",
      "Backend заранее создаёт календарные reward payout и показывает их в подписке.",
    ],
    [
      "5",
      "Создайте заявку на вывод",
      "Средства блокируются, а администратор отправляет USDT вручную.",
    ],
  ];
  return (
    <section className="section page-hero">
      <div className="container narrow">
        <p className="eyebrow">Как это работает</p>
        <h1>Путь клиента от регистрации до вывода</h1>
        <div className="timeline">
          {steps.map(([number, title, text]) => (
            <div className="timeline-item" key={number}>
              <span>{number}</span>
              <div>
                <h2>{title}</h2>
                <p>{text}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="notice info">
          <strong>30 минут и 24 часа</strong>
          <p>
            Первые 30 минут — основной срок заявки. Точная сумма остаётся
            закреплена за пользователем 24 часа и может быть зачислена
            автоматически даже после завершения основного срока.
          </p>
        </div>
        <Link className="button button-primary" to="/plans">
          Посмотреть программы
        </Link>
      </div>
    </section>
  );
}
