import { Link } from "react-router-dom";
export function NotFoundPage() {
  return (
    <main className="page-center">
      <div>
        <h1>Страница не найдена</h1>
        <p>Проверьте адрес или вернитесь в панель.</p>
        <Link className="button button-primary" to="/">
          На главную
        </Link>
      </div>
    </main>
  );
}
