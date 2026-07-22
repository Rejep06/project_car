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
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  if (user) return <Navigate to="/account" replace />;
  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      const from = (location.state as { from?: string } | null)?.from;
      navigate(from || "/account", { replace: true });
    } catch (e) {
      setError(e instanceof ApiClientError ? e.message : "Не удалось войти");
    } finally {
      setLoading(false);
    }
  }
  return (
    <section className="auth-page">
      <Card className="auth-card">
        <p className="eyebrow">Личный кабинет</p>
        <h1>Вход</h1>
        <p>Используйте email и пароль, указанные при регистрации.</p>
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
          {error && (
            <div className="form-error" role="alert">
              {error}
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
