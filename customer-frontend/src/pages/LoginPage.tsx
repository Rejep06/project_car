import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [emailNotVerified, setEmailNotVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  if (user) return <Navigate to="/account" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setEmailNotVerified(false);
    try {
      await login(email, password);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from || "/account", { replace: true });
    } catch (e) {
      if (e instanceof ApiClientError) {
        setEmailNotVerified(e.code === "email_not_verified");
        setError(e.message);
      } else {
        setError("Не удалось войти");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <Card className="auth-card">
        <p className="eyebrow">Личный кабинет</p>
        <h1>Вход</h1>
        <p>Используйте подтверждённый email и пароль.</p>
        <form onSubmit={submit} className="form-stack">
          <label>
            Email
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Пароль
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <div className="form-row-link">
            <Link to="/forgot-password">Забыли пароль?</Link>
          </div>
          {error && (
            <div className="form-error" role="alert">
              {error}
              {emailNotVerified && email && (
                <div>
                  <Link to={`/check-email?email=${encodeURIComponent(email)}`}>
                    Отправить письмо повторно
                  </Link>
                </div>
              )}
            </div>
          )}
          <Button type="submit" loading={loading}>
            Войти
          </Button>
        </form>
        <p>
          Нет аккаунта? <Link to="/register">Создать</Link>
        </p>
      </Card>
    </section>
  );
}
