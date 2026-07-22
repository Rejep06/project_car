import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createPlan, getPlan, updatePlan } from "../api/plans";
import type { DurationUnit, PlanInput, RewardFrequency } from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { formatMoney } from "../utils/money";
import { label } from "../utils/labels";
const initial: PlanInput = {
  title: "",
  slug: "",
  category: "game",
  short_description: "",
  full_description: "",
  image_url: null,
  price: "",
  access_duration_value: 1,
  access_duration_unit: "month",
  reward_amount: "",
  reward_frequency: "monthly",
  reward_duration_value: 1,
  reward_duration_unit: "month",
  is_active: true,
};
export function PlanFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState<PlanInput>(initial);
  const [loading, setLoading] = useState(Boolean(id));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!id) return;
    getPlan(id)
      .then((p) => setForm({ ...p, image_url: p.image_url }))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);
  const previewPrice = useMemo(() => {
    try {
      return formatMoney(form.price || "0");
    } catch {
      return "Некорректная сумма";
    }
  }, [form.price]);
  const previewReward = useMemo(() => {
    try {
      return formatMoney(form.reward_amount || "0");
    } catch {
      return "Некорректная сумма";
    }
  }, [form.reward_amount]);
  function set<K extends keyof PlanInput>(key: K, value: PlanInput[K]) {
    setForm((v) => ({ ...v, [key]: value }));
  }
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (id) await updatePlan(id, form);
      else await createPlan({ ...form, is_active: form.is_active ?? true });
      navigate("/plans");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <LoadingSpinner />;
  return (
    <>
      <PageHeader
        title={id ? "Изменение подписки" : "Новая подписка"}
        description="Денежные значения передаются backend строками, без JavaScript float."
        actions={
          <Link className="button button-secondary" to="/plans">
            Назад
          </Link>
        }
      />
      <form className="editor-grid" onSubmit={submit}>
        <div className="form-sections">
          <Card>
            <h2>Основная информация</h2>
            <div className="form-grid">
              <FormField label="Название">
                <input
                  value={form.title}
                  onChange={(e) => set("title", e.target.value)}
                  required
                />
              </FormField>
              <FormField label="Slug" hint="Латиница, цифры и дефис">
                <input
                  value={form.slug}
                  onChange={(e) => set("slug", e.target.value)}
                  pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                  required
                />
              </FormField>
              <FormField label="Тип программы (служебный)">
                <select
                  value={form.category}
                  onChange={(e) =>
                    set("category", e.target.value as PlanInput["category"])
                  }
                >
                  <option value="game">Основная программа</option>
                  <option value="application">Расширенная программа</option>
                </select>
              </FormField>
              <FormField label="URL изображения">
                <input
                  type="url"
                  value={form.image_url ?? ""}
                  onChange={(e) => set("image_url", e.target.value || null)}
                />
              </FormField>
            </div>
            <FormField label="Краткое описание">
              <textarea
                rows={3}
                value={form.short_description}
                onChange={(e) => set("short_description", e.target.value)}
              />
            </FormField>
            <FormField label="Полное описание">
              <textarea
                rows={8}
                value={form.full_description}
                onChange={(e) => set("full_description", e.target.value)}
              />
            </FormField>
          </Card>
          <Card>
            <h2>Стоимость и срок программы</h2>
            <div className="form-grid">
              <FormField label="Стоимость, USDT">
                <input
                  inputMode="decimal"
                  value={form.price}
                  onChange={(e) => set("price", e.target.value)}
                  required
                />
              </FormField>
              <FormField label="Срок">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={form.access_duration_value}
                  onChange={(e) =>
                    set("access_duration_value", e.currentTarget.valueAsNumber)
                  }
                  required
                />
              </FormField>
              <FormField label="Единица срока">
                <select
                  value={form.access_duration_unit}
                  onChange={(e) =>
                    set("access_duration_unit", e.target.value as DurationUnit)
                  }
                >
                  {["day", "week", "month", "year"].map((x) => (
                    <option key={x} value={x}>
                      {label(x)}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
          </Card>
          <Card>
            <h2>Вознаграждения</h2>
            <div className="form-grid">
              <FormField label="Сумма одного начисления, USDT">
                <input
                  inputMode="decimal"
                  value={form.reward_amount}
                  onChange={(e) => set("reward_amount", e.target.value)}
                  required
                />
              </FormField>
              <FormField label="Частота">
                <select
                  value={form.reward_frequency}
                  onChange={(e) =>
                    set("reward_frequency", e.target.value as RewardFrequency)
                  }
                >
                  {["daily", "weekly", "monthly"].map((x) => (
                    <option key={x} value={x}>
                      {label(x)}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField label="Длительность начислений">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={form.reward_duration_value}
                  onChange={(e) =>
                    set("reward_duration_value", e.currentTarget.valueAsNumber)
                  }
                  required
                />
              </FormField>
              <FormField label="Единица длительности">
                <select
                  value={form.reward_duration_unit}
                  onChange={(e) =>
                    set("reward_duration_unit", e.target.value as DurationUnit)
                  }
                >
                  {["day", "week", "month", "year"].map((x) => (
                    <option key={x} value={x}>
                      {label(x)}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>
          </Card>
          {!id && (
            <Card>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(form.is_active)}
                  onChange={(e) => set("is_active", e.target.checked)}
                />
                Сразу активировать программу
              </label>
            </Card>
          )}
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <Button type="submit" loading={busy}>
              Сохранить
            </Button>
          </div>
        </div>
        <aside>
          <Card className="preview-card">
            <h2>Предварительный просмотр</h2>
            {form.image_url && (
              <img src={form.image_url} alt="Предварительный просмотр" />
            )}
            <h3>{form.title || "Название программы"}</h3>
            <p>{form.short_description || "Краткое описание программы."}</p>
            <dl>
              <div>
                <dt>Стоимость</dt>
                <dd>{previewPrice} USDT</dd>
              </div>
              <div>
                <dt>Срок</dt>
                <dd>
                  {form.access_duration_value}{" "}
                  {label(form.access_duration_unit)}
                </dd>
              </div>
              <div>
                <dt>Вознаграждение</dt>
                <dd>
                  {previewReward} USDT · {label(form.reward_frequency)}
                </dd>
              </div>
            </dl>
          </Card>
        </aside>
      </form>
    </>
  );
}
