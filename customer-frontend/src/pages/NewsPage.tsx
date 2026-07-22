import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listPosts } from "../api/posts";
import type { Post } from "../api/types";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { Pagination } from "../components/Pagination";
import { formatDateOnly } from "../utils/date";

export function NewsPage() {
  const [items, setItems] = useState<Post[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    setLoading(true);
    listPosts(page, 9)
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
        setError("");
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page]);
  return (
    <section className="section page-hero">
      <div className="container">
        <div className="section-heading">
          <p className="eyebrow">Новости</p>
          <h1>Публикации автомобильной компании</h1>
          <p>На сайте показываются только опубликованные материалы.</p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="notice danger">{error}</div>
        ) : items.length ? (
          <>
            <div className="news-grid">
              {items.map((post) => (
                <Card className="news-card" key={post.id}>
                  <p className="small muted">
                    {formatDateOnly(post.published_at)}
                  </p>
                  <h2>{post.title}</h2>
                  <p>{post.excerpt}</p>
                  <Link to={`/news/${post.slug}`}>Читать →</Link>
                </Card>
              ))}
            </div>
            <Pagination
              page={page}
              pageSize={9}
              total={total}
              onChange={setPage}
            />
          </>
        ) : (
          <EmptyState
            title="Новостей пока нет"
            text="Опубликованные новости появятся здесь."
          />
        )}
      </div>
    </section>
  );
}
