import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmPasswordReset } from "../api/auth";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) {
      setMessage("В ссылке отсутствует токен восстановления.");
      return;
    }
    if (password !== confirm) {
      setMessage("Пароли не совпадают");
      return;
    }
    setLoading(true);
    try {
      const result = await confirmPasswordReset(token, password);
      setSuccess(true);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось изменить пароль");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <Card className="auth-card">
        <p className="eyebrow">Новый пароль</p>
        <h1>Восстановление доступа</h1>
        {!success ? (
          <form className="form-stack" onSubmit={submit}>
            <label>
              Новый пароль
              <input type="password" minLength={8} required value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            <label>
              Повторите пароль
              <input type="password" minLength={8} required value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </label>
            <Button type="submit" loading={loading}>Сохранить пароль</Button>
          </form>
        ) : null}
        {message && <div className={success ? "notice success" : "form-error"}>{message}</div>}
        {success && <Link className="button button-primary" to="/login">Войти</Link>}
      </Card>
    </section>
  );
}
