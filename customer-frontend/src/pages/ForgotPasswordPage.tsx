import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { requestPasswordReset } from "../api/auth";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const result = await requestPasswordReset(email);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось отправить письмо");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <Card className="auth-card">
        <p className="eyebrow">Восстановление доступа</p>
        <h1>Забыли пароль?</h1>
        <p>Укажите email. Мы отправим ссылку для создания нового пароля.</p>
        <form className="form-stack" onSubmit={submit}>
          <label>
            Email
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <Button type="submit" loading={loading}>Отправить ссылку</Button>
        </form>
        {message && <div className="notice">{message}</div>}
        <Link to="/login">Вернуться ко входу</Link>
      </Card>
    </section>
  );
}
