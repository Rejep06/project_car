import { Button } from "./Button";

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <nav className="pagination" aria-label="Пагинация">
      <Button
        variant="secondary"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Назад
      </Button>
      <span>
        Страница {page} из {pages}
      </span>
      <Button
        variant="secondary"
        onClick={() => onChange(page + 1)}
        disabled={page >= pages}
      >
        Далее
      </Button>
    </nav>
  );
}
