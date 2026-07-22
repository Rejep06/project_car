import { Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { archivePost, listPosts, publishPost } from "../api/posts";
import type { Post } from "../api/types";
import { Button } from "../components/Button";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
export function PostsPage() {
  const [items, setItems] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(() => {
    setLoading(true);
    listPosts(page, 20)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  useEffect(load, [load]);
  async function action(post: Post) {
    try {
      await (post.status === "published"
        ? archivePost(post.id)
        : publishPost(post.id));
      setMessage(
        post.status === "published"
          ? "Новость архивирована"
          : "Новость опубликована",
      );
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }
  return (
    <>
      <PageHeader
        title="Новости"
        description="Черновики, публикация и архивирование материалов компании."
        actions={
          <Link className="button button-primary" to="/posts/new">
            <Plus />
            Создать новость
          </Link>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState
          title="Новостей нет"
          description="Создайте первый черновик."
        />
      ) : (
        <>
          <DataTable label="Новости">
            <thead>
              <tr>
                <th>Заголовок</th>
                <th>Slug</th>
                <th>Статус</th>
                <th>Опубликовано</th>
                <th>Изменено</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.title}</strong>
                    <small>{p.excerpt}</small>
                  </td>
                  <td className="mono">{p.slug}</td>
                  <td>
                    <StatusBadge value={p.status} />
                  </td>
                  <td>{formatDateTime(p.published_at)}</td>
                  <td>{formatDateTime(p.updated_at)}</td>
                  <td className="row-actions">
                    <Link to={`/posts/${p.id}`}>Изменить</Link>
                    {p.status !== "archived" && (
                      <Button variant="ghost" onClick={() => action(p)}>
                        {p.status === "published"
                          ? "Архивировать"
                          : "Опубликовать"}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <Pagination
            page={page}
            pageSize={20}
            total={total}
            onChange={setPage}
          />
        </>
      )}
    </>
  );
}
