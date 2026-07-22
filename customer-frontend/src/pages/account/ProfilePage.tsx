import { useState, type FormEvent } from "react";
import { updateMe } from "../../api/users";
import { useAuth } from "../../auth/AuthContext";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";
export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [email, setEmail] = useState(user?.email ?? "");
  const [loading, setLoading] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await updateMe(email);
      await refreshUser();
      showToast("Профиль обновлён", "success");
    } catch (err) {
      showToast(
        err instanceof Error ? err.message : "Не удалось обновить профиль",
        "error",
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Учётная запись</p>
          <h1>Профиль</h1>
        </div>
      </div>
      <div className="two-column align-start">
        <Card>
          <h2>Основные данные</h2>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <Button type="submit" loading={loading}>
              Сохранить
            </Button>
          </form>
        </Card>
        <Card>
          <h2>Статус аккаунта</h2>
          <dl className="compact-dl">
            <div>
              <dt>Роль</dt>
              <dd>{user?.role}</dd>
            </div>
            <div>
              <dt>Активность</dt>
              <dd>
                <StatusBadge
                  status={user?.is_active ? "active" : "cancelled"}
                />
              </dd>
            </div>
            <div>
              <dt>Операции</dt>
              <dd>{user?.is_frozen ? "Заморожены" : "Разрешены"}</dd>
            </div>
            <div>
              <dt>Создан</dt>
              <dd>{formatDate(user?.created_at)}</dd>
            </div>
          </dl>
        </Card>
      </div>
    </div>
  );
}
