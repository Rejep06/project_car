import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createPost, getPost, updatePost } from "../api/posts";
import type { PostInput } from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
const initial: PostInput = {
  title: "",
  slug: "",
  excerpt: "",
  content: "",
  cover_image_url: null,
};
export function PostFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState<PostInput>(initial);
  const [loading, setLoading] = useState(Boolean(id));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!id) return;
    getPost(id)
      .then((p) =>
        setForm({
          title: p.title,
          slug: p.slug,
          excerpt: p.excerpt,
          content: p.content,
          cover_image_url: p.cover_image_url,
        }),
      )
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);
  function set<K extends keyof PostInput>(key: K, value: PostInput[K]) {
    setForm((v) => ({ ...v, [key]: value }));
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      if (id) await updatePost(id, form);
      else await createPost(form);
      navigate("/posts");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка сохранения");
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <LoadingSpinner />;
  return (
    <>
      <PageHeader
        title={id ? "Изменение новости" : "Новая новость"}
        description="Обычный textarea без тяжёлого визуального редактора."
        actions={
          <Link className="button button-secondary" to="/posts">
            Назад
          </Link>
        }
      />
      <form className="editor-grid" onSubmit={submit}>
        <Card>
          <div className="form-grid">
            <FormField label="Заголовок">
              <input
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
                required
              />
            </FormField>
            <FormField label="Slug">
              <input
                value={form.slug}
                onChange={(e) => set("slug", e.target.value)}
                pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                required
              />
            </FormField>
            <FormField label="URL обложки">
              <input
                type="url"
                value={form.cover_image_url ?? ""}
                onChange={(e) => set("cover_image_url", e.target.value || null)}
              />
            </FormField>
          </div>
          <FormField label="Краткое описание">
            <textarea
              rows={3}
              value={form.excerpt}
              onChange={(e) => set("excerpt", e.target.value)}
            />
          </FormField>
          <FormField label="Содержимое (Markdown хранится как текст)">
            <textarea
              rows={16}
              value={form.content}
              onChange={(e) => set("content", e.target.value)}
              required
            />
          </FormField>
          {error && <p className="form-error">{error}</p>}
          <Button type="submit" loading={busy}>
            Сохранить черновик
          </Button>
        </Card>
        <aside>
          <Card className="post-preview">
            {form.cover_image_url && (
              <img src={form.cover_image_url} alt="Обложка" />
            )}
            <small>Предварительный просмотр</small>
            <h2>{form.title || "Заголовок новости"}</h2>
            <p>{form.excerpt || "Краткое описание"}</p>
            <div className="preview-content">
              {form.content || "Текст новости"}
            </div>
          </Card>
        </aside>
      </form>
    </>
  );
}
