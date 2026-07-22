import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { adjustBalance, freezeUser, getUser, unfreezeUser } from "../api/users";
import type { AdminUser } from "../api/types";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";
import { formatMoney } from "../utils/money";
export function UserDetailsPage() {
  const { id = "" } = useParams();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    getUser(id)
      .then(setUser)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);
  async function toggle() {
    if (!user) return;
    setBusy(true);
    try {
      setUser(await (user.is_frozen ? unfreezeUser(id) : freezeUser(id)));
      setMessage(
        user.is_frozen ? "Пользователь разморожен" : "Пользователь заморожен",
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
      setConfirm(false);
    }
  }
  async function adjust(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      setUser(
        await adjustBalance(id, amount, description, crypto.randomUUID()),
      );
      setMessage("Корректировка записана через WalletService");
      setAmount("");
      setDescription("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  if (loading) return <LoadingSpinner />;
  if (!user)
    return (
      <>
        <PageHeader title="Пользователь не найден" />
        <p>{error}</p>
      </>
    );
  return (
    <>
      <PageHeader
        title={user.email}
        description={user.id}
        actions={
          <>
            <Link className="button button-secondary" to="/users">
              Назад
            </Link>
            <Button
              variant={user.is_frozen ? "primary" : "danger"}
              onClick={() => setConfirm(true)}
            >
              {user.is_frozen ? "Разморозить" : "Заморозить"}
            </Button>
          </>
        }
      />
      {message && <Toast message={message} />}{" "}
      {error && <Toast message={error} type="error" />}
      <div className="detail-grid">
        <Card>
          <h2>Профиль</h2>
          <dl className="details">
            <div>
              <dt>Роль</dt>
              <dd>
                <StatusBadge value={user.role} />
              </dd>
            </div>
            <div>
              <dt>Активен</dt>
              <dd>{user.is_active ? "Да" : "Нет"}</dd>
            </div>
            <div>
              <dt>Заморожен</dt>
              <dd>{user.is_frozen ? "Да" : "Нет"}</dd>
            </div>
            <div>
              <dt>Создан</dt>
              <dd>{formatDateTime(user.created_at)}</dd>
            </div>
            <div>
              <dt>Изменён</dt>
              <dd>{formatDateTime(user.updated_at)}</dd>
            </div>
          </dl>
        </Card>
        <Card>
          <h2>Кошелёк</h2>
          <div className="balance-panels">
            <div>
              <small>Доступно</small>
              <strong>
                {formatMoney(user.available_balance)} {user.asset}
              </strong>
            </div>
            <div>
              <small>Заблокировано</small>
              <strong>
                {formatMoney(user.locked_balance)} {user.asset}
              </strong>
            </div>
          </div>
        </Card>
      </div>
      <Card>
        <h2>Административная корректировка</h2>
        <p className="muted">
          Это не прямое присваивание баланса. Backend блокирует кошелёк, создаёт
          WalletTransaction и AuditLog. Для списания укажите отрицательную
          сумму.
        </p>
        <form className="inline-form" onSubmit={adjust}>
          <FormField label="Сумма, USDT">
            <input
              inputMode="decimal"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </FormField>
          <FormField label="Причина">
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              minLength={3}
              required
            />
          </FormField>
          <Button type="submit" loading={busy}>
            Выполнить корректировку
          </Button>
        </form>
      </Card>
      <Card>
        <h2>Связанные данные</h2>
        <p className="muted">
          Текущий backend не предоставляет административные subresource
          endpoints для подписок, операций, пополнений, выводов и обращений
          одного пользователя. Панель не создаёт несуществующие запросы;
          переходите в соответствующие общие разделы.
        </p>
        <div className="link-row">
          <Link to="/deposits">Пополнения</Link>
          <Link to="/withdrawals">Выводы</Link>
          <Link to="/support">Поддержка</Link>
          <Link to="/audit">Аудит</Link>
        </div>
      </Card>
      <ConfirmDialog
        open={confirm}
        title={
          user.is_frozen
            ? "Разморозить пользователя"
            : "Заморозить пользователя"
        }
        description="Backend повторно проверит роль администратора и текущее состояние пользователя."
        confirmLabel={user.is_frozen ? "Разморозить" : "Заморозить"}
        danger={!user.is_frozen}
        loading={busy}
        onConfirm={toggle}
        onClose={() => setConfirm(false)}
      />
    </>
  );
}
