import { MailCheck, MailWarning } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { updateMe } from "../../api/users";
import { useAuth } from "../../auth/AuthContext";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { StatusBadge } from "../../components/StatusBadge";
import { showToast } from "../../components/Toast";
import { formatDate } from "../../utils/date";

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [email, setEmail] = useState(user?.pending_email ?? user?.email ?? "");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setEmail(user?.pending_email ?? user?.email ?? "");
  }, [user?.email, user?.pending_email]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const updated = await updateMe(email);
      await refreshUser();
      if (updated.pending_email) {
        showToast(
          `Письмо для подтверждения отправлено на ${updated.pending_email}`,
          "success",
        );
      } else {
        showToast("Профиль обновлён", "success");
      }
    } catch (error) {
      showToast(
        error instanceof Error ? error.message : "Не удалось обновить профиль",
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
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <p className="field-hint">
              При смене адреса мы отправим письмо. Текущий email будет действовать,
              пока новый адрес не подтверждён.
            </p>
            <Button type="submit" loading={loading}>
              Сохранить
            </Button>
          </form>
          {user?.pending_email ? (
            <div className="notice warning email-state-notice">
              <MailWarning size={20} />
              <div>
                <strong>Ожидается подтверждение нового email</strong>
                <p>{user.pending_email}</p>
              </div>
            </div>
          ) : null}
        </Card>
        <Card>
          <h2>Статус аккаунта</h2>
          <dl className="compact-dl">
            <div>
              <dt>Email</dt>
              <dd className="email-verification-state">
                {user?.email_verified ? (
                  <><MailCheck size={18} /> Подтверждён</>
                ) : (
                  <><MailWarning size={18} /> Не подтверждён</>
                )}
              </dd>
            </div>
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
