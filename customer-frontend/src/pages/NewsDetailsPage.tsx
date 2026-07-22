import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getPost } from "../api/posts";
import type { Post } from "../api/types";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { formatDateOnly } from "../utils/date";

export function NewsDetailsPage() {
  const { slug = "" } = useParams();
  const [post, setPost] = useState<Post | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getPost(slug)
      .then(setPost)
      .catch((e: Error) => setError(e.message));
  }, [slug]);
  if (error)
    return (
      <section className="section">
        <div className="container notice danger">{error}</div>
      </section>
    );
  if (!post)
    return (
      <div className="page-center">
        <LoadingSpinner />
      </div>
    );
  return (
    <article className="section article-page">
      <div className="container narrow">
        <Link to="/news">← Все новости</Link>
        <p className="eyebrow">{formatDateOnly(post.published_at)}</p>
        <h1>{post.title}</h1>
        <p className="lead">{post.excerpt}</p>
        {post.cover_image_url && (
          <img className="article-cover" src={post.cover_image_url} alt="" />
        )}
        <div className="article-content">
          {post.content
            .split("\n")
            .map((p, i) =>
              p ? <p key={`${i}-${p.slice(0, 20)}`}>{p}</p> : null,
            )}
        </div>
      </div>
    </article>
  );
}
