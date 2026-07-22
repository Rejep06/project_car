import { Link } from "react-router-dom";
export function NotFoundPage() {
  return (
    <section className="section">
      <div className="container empty-state">
        <h1>Страница не найдена</h1>
        <p>Проверьте адрес или вернитесь на главную.</p>
        <Link className="button button-primary" to="/">
          На главную
        </Link>
      </div>
    </section>
  );
}
