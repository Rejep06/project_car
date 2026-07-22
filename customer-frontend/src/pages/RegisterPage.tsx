import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function RegisterPage() {
  const { user, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  if (user) return <Navigate to="/account" replace />;
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await register(email, password);
      navigate("/account", { replace: true });
    } catch (e) {
      setError(
        e instanceof ApiClientError
          ? e.message
          : "Не удалось зарегистрироваться",
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <section className="auth-page">
      <Card className="auth-card">
        <p className="eyebrow">Новый клиент</p>
        <h1>Создание аккаунта</h1>
        <p>После регистрации для клиента создаётся внутренний баланс.</p>
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
              minLength={8}
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <span className="field-hint">Минимум 8 символов</span>
          </label>
          <label>
            Повторите пароль
            <input
              type="password"
              minLength={8}
              required
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </label>
          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}
          <Button type="submit" loading={loading}>
            Создать аккаунт
          </Button>
        </form>
        <p>
          Уже зарегистрированы? <Link to="/login">Войти</Link>
        </p>
      </Card>
    </section>
  );
}
