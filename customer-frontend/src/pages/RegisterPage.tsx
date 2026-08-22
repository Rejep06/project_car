import { Gift, ShieldCheck, UserPlus } from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import {
  Link,
  Navigate,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { Card } from "../components/Card";

export function RegisterPage() {
  const { user, register } = useAuth();
  const [searchParams] = useSearchParams();
  const linkReferralCode = useMemo(
    () => (searchParams.get("ref") || "").trim().toUpperCase(),
    [searchParams],
  );
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [referralCode, setReferralCode] = useState(linkReferralCode);
  const [acceptContractDocuments, setAcceptContractDocuments] = useState(false);
  const [acceptPrivacyDocuments, setAcceptPrivacyDocuments] = useState(false);
  const [confirmEligibility, setConfirmEligibility] = useState(false);
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
    if (
      !acceptContractDocuments ||
      !acceptPrivacyDocuments ||
      !confirmEligibility
    ) {
      setError("Для регистрации подтвердите три обязательных пункта");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await register(
        email,
        password,
        {
          // Три видимые группы согласий фиксируются в базе как пять отдельных
          // документов с собственными версиями: это сохраняет подробный аудит.
          accept_terms: true,
          accept_privacy_policy: true,
          accept_personal_data_processing: true,
          accept_program_rules: true,
          confirm_age_18: true,
        },
        referralCode.trim() || undefined,
      );
      navigate(`/check-email?email=${encodeURIComponent(result.email)}`, {
        replace: true,
        state: { debugToken: result.debug_verification_token },
      });
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
      <Card className="auth-card auth-card-wide">
        <p className="eyebrow">Новый клиент</p>
        <h1>Создание аккаунта</h1>
        <p>
          После регистрации мы отправим письмо. Войти в личный кабинет можно
          только после подтверждения email.
        </p>
        {linkReferralCode && (
          <div className="notice success referral-invite-notice">
            <UserPlus size={20} />
            <div>
              <strong>Вы регистрируетесь по приглашению</strong>
              <p>Реферальный код уже добавлен в форму.</p>
            </div>
          </div>
        )}
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
          <label>
            Реферальный код
            <input
              value={referralCode}
              maxLength={20}
              autoComplete="off"
              placeholder="Необязательно"
              onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
            />
            <span className="field-hint">
              <Gift size={14} /> Укажите код человека, который вас пригласил.
            </span>
          </label>

          <div className="legal-consents" aria-label="Обязательные согласия">
            <div className="legal-consents-heading">
              <ShieldCheck size={20} aria-hidden="true" />
              <div>
                <strong>Обязательные подтверждения</strong>
                <p>Документы откроются в новой вкладке.</p>
              </div>
            </div>

            <label className="checkbox-row">
              <input
                type="checkbox"
                required
                checked={acceptContractDocuments}
                onChange={(e) => setAcceptContractDocuments(e.target.checked)}
              />
              <span>
                Я принимаю{" "}
                <Link to="/terms" target="_blank" rel="noreferrer">
                  Пользовательское соглашение
                </Link>{" "}
                и{" "}
                <Link to="/program-rules" target="_blank" rel="noreferrer">
                  Правила клиентских программ и лотерей
                </Link>
                , включая условия оплаты, начислений, возвратов, участия в
                розыгрышах и получения призов.
              </span>
            </label>

            <label className="checkbox-row">
              <input
                type="checkbox"
                required
                checked={acceptPrivacyDocuments}
                onChange={(e) => setAcceptPrivacyDocuments(e.target.checked)}
              />
              <span>
                Я ознакомился с{" "}
                <Link to="/privacy" target="_blank" rel="noreferrer">
                  Политикой конфиденциальности
                </Link>{" "}
                и даю согласие на обработку персональных данных на условиях{" "}
                <Link
                  to="/personal-data-consent"
                  target="_blank"
                  rel="noreferrer"
                >
                  отдельного Согласия
                </Link>
                .
              </span>
            </label>

            <label className="checkbox-row">
              <input
                type="checkbox"
                required
                checked={confirmEligibility}
                onChange={(e) => setConfirmEligibility(e.target.checked)}
              />
              <span>
                Я подтверждаю, что мне исполнилось 18 лет, я полностью
                дееспособен, действую от своего имени, предоставляю достоверные
                сведения и вправе пользоваться сервисом по применимому
                законодательству.
              </span>
            </label>

            <p className="legal-consent-evidence">
              При регистрации фиксируются версии документов, формулировки
              согласий, дата и время, email аккаунта, IP-адрес и данные браузера.
            </p>
          </div>

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
