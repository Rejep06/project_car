import { CircleCheck, CircleX } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { confirmEmail } from "../api/auth";
import { Card } from "../components/Card";
import { LoadingSpinner } from "../components/LoadingSpinner";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Проверяем ссылку…");

  useEffect(() => {
    let active = true;
    if (!token) {
      setStatus("error");
      setMessage("В ссылке отсутствует токен подтверждения.");
      return undefined;
    }
    confirmEmail(token)
      .then((result) => {
        if (!active) return;
        setStatus("success");
        setMessage(result.message);
      })
      .catch((error: unknown) => {
        if (!active) return;
        setStatus("error");
        setMessage(error instanceof Error ? error.message : "Не удалось подтвердить email");
      });
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <section className="auth-page">
      <Card className="auth-card verification-card">
        {status === "loading" && <LoadingSpinner />}
        {status === "success" && <CircleCheck size={48} />}
        {status === "error" && <CircleX size={48} />}
        <h1>{status === "success" ? "Email подтверждён" : status === "error" ? "Ссылка не сработала" : "Подтверждение email"}</h1>
        <p>{message}</p>
        <Link className="button button-primary" to="/login">Войти</Link>
      </Card>
    </section>
  );
}
