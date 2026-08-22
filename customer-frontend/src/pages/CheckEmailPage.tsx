import { MailCheck } from "lucide-react";
import { useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { resendEmailVerification } from "../api/auth";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function CheckEmailPage() {
  const [params] = useSearchParams();
  const location = useLocation();
  const email = params.get("email") || "";
  const debugToken = (location.state as { debugToken?: string | null } | null)
    ?.debugToken;
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function resend() {
    if (!email) return;
    setLoading(true);
    try {
      const result = await resendEmailVerification(email);
      setMessage(result.message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Не удалось отправить письмо");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-page">
      <Card className="auth-card verification-card">
        <MailCheck size={44} />
        <p className="eyebrow">Подтверждение email</p>
        <h1>Проверьте почту</h1>
        <p>
          Ссылка для подтверждения отправлена на <strong>{email || "указанный email"}</strong>.
          После подтверждения вернитесь на страницу входа.
        </p>
        <p className="field-hint">Проверьте также папки «Спам» и «Промоакции».</p>
        {debugToken && (
          <Link className="button button-primary" to={`/verify-email?token=${encodeURIComponent(debugToken)}`}>
            Подтвердить тестовый аккаунт
          </Link>
        )}
        {email && (
          <Button variant="secondary" loading={loading} onClick={() => void resend()}>
            Отправить письмо повторно
          </Button>
        )}
        {message && <div className="notice">{message}</div>}
        <Link to="/login">Перейти ко входу</Link>
      </Card>
    </section>
  );
}
