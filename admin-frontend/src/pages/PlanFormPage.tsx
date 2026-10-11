import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createPlan, getPlan, updatePlan } from "../api/plans";
import type {
  DurationUnit,
  PlanInput,
  PlanTier,
  RewardFrequency,
} from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { defaultProgramImageUrl } from "../config/assets";
import { label } from "../utils/labels";
import { formatMoney } from "../utils/money";

const initial: PlanInput = {
  title: "",
  tier: "starter",
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

const tiers: PlanTier[] = ["starter", "standard", "premium"];

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
      .then((plan) =>
        setForm({
          title: plan.title,
          tier: plan.tier,
          short_description: plan.short_description,
          full_description: plan.full_description,
          image_url: plan.image_url,
          price: plan.price,
          access_duration_value: plan.access_duration_value,
          access_duration_unit: plan.access_duration_unit,
          reward_amount: plan.reward_amount,
          reward_frequency: plan.reward_frequency,
          reward_duration_value: plan.reward_duration_value,
          reward_duration_unit: plan.reward_duration_unit,
          is_active: plan.is_active,
        }),
      )
      .catch((requestError) => setError(requestError.message))
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
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (id) {
        const changes = { ...form };
        delete changes.is_active;
        await updatePlan(id, changes);
      } else {
        await createPlan({ ...form, is_active: form.is_active ?? true });
      }
      navigate("/plans");
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Не удалось сохранить программу",
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <>
      <PageHeader
        title={id ? "Изменение программы" : "Новая программа"}
        description="Заполните название, описание, фотографию и условия клиентской программы."
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
                  onChange={(event) => set("title", event.target.value)}
                  required
                />
              </FormField>
              <FormField
                label="Уровень программы"
                hint="Старт — начальный уровень, Стандарт — основной, Премиум — максимальный."
              >
                <select
                  value={form.tier}
                  onChange={(event) =>
                    set("tier", event.target.value as PlanTier)
                  }
                >
                  {tiers.map((tier) => (
                    <option key={tier} value={tier}>
                      {label(tier)}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField
                label="URL фотографии"
                hint="Прямая ссылка на JPG, PNG или WebP. Если оставить поле пустым, будет показана стандартная фотография."
              >
                <input
                  type="url"
                  value={form.image_url ?? ""}
                  onChange={(event) =>
                    set("image_url", event.target.value || null)
                  }
                />
              </FormField>
            </div>
            <FormField label="Краткое описание">
              <textarea
                rows={3}
                value={form.short_description}
                onChange={(event) =>
                  set("short_description", event.target.value)
                }
                required
              />
            </FormField>
            <FormField label="Полное описание">
              <textarea
                rows={8}
                value={form.full_description}
                onChange={(event) =>
                  set("full_description", event.target.value)
                }
                required
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
                  onChange={(event) => set("price", event.target.value)}
                  required
                />
              </FormField>
              <FormField label="Срок доступа">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={form.access_duration_value}
                  onChange={(event) =>
                    set(
                      "access_duration_value",
                      event.currentTarget.valueAsNumber,
                    )
                  }
                  required
                />
              </FormField>
              <FormField label="Единица срока">
                <select
                  value={form.access_duration_unit}
                  onChange={(event) =>
                    set(
                      "access_duration_unit",
                      event.target.value as DurationUnit,
                    )
                  }
                >
                  {(["day", "week", "month", "year"] as DurationUnit[]).map(
                    (unit) => (
                      <option key={unit} value={unit}>
                        {label(unit)}
                      </option>
                    ),
                  )}
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
                  onChange={(event) =>
                    set("reward_amount", event.target.value)
                  }
                  required
                />
              </FormField>
              <FormField label="Частота начислений">
                <select
                  value={form.reward_frequency}
                  onChange={(event) =>
                    set(
                      "reward_frequency",
                      event.target.value as RewardFrequency,
                    )
                  }
                >
                  {(
                    ["daily", "weekly", "monthly"] as RewardFrequency[]
                  ).map((frequency) => (
                    <option key={frequency} value={frequency}>
                      {label(frequency)}
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
                  onChange={(event) =>
                    set(
                      "reward_duration_value",
                      event.currentTarget.valueAsNumber,
                    )
                  }
                  required
                />
              </FormField>
              <FormField label="Единица длительности">
                <select
                  value={form.reward_duration_unit}
                  onChange={(event) =>
                    set(
                      "reward_duration_unit",
                      event.target.value as DurationUnit,
                    )
                  }
                >
                  {(["day", "week", "month", "year"] as DurationUnit[]).map(
                    (unit) => (
                      <option key={unit} value={unit}>
                        {label(unit)}
                      </option>
                    ),
                  )}
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
                  onChange={(event) =>
                    set("is_active", event.target.checked)
                  }
                />
                Сразу опубликовать программу
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
            <img
              src={form.image_url || defaultProgramImageUrl}
              alt="Предварительный просмотр фотографии программы"
              onError={(event) => {
                event.currentTarget.onerror = null;
                event.currentTarget.src = defaultProgramImageUrl;
              }}
            />
            <span className={`tier-pill tier-pill-${form.tier}`}>
              {label(form.tier)}
            </span>
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
                  {form.access_duration_value} {label(form.access_duration_unit)}
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
