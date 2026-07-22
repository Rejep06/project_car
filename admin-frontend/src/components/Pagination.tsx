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
  if (total <= pageSize) return null;
  return (
    <nav className="pagination" aria-label="Пагинация">
      <button
        type="button"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
      >
        Назад
      </button>
      <span>
        Страница {page} из {pages}
      </span>
      <button
        type="button"
        onClick={() => onChange(page + 1)}
        disabled={page >= pages}
      >
        Далее
      </button>
    </nav>
  );
}
