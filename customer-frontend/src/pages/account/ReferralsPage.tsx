import {
  CheckCircle2,
  Gift,
  Link2,
  Share2,
  Sparkles,
  UserPlus,
  UsersRound,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { getReferralSummary } from "../../api/referrals";
import type { ReferralSummary } from "../../api/types";
import { Card } from "../../components/Card";
import { CopyButton } from "../../components/CopyButton";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { formatDateOnly } from "../../utils/date";

export function ReferralsPage() {
  const [summary, setSummary] = useState<ReferralSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getReferralSummary()
      .then(setSummary)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const referralLink = useMemo(() => {
    if (!summary) return "";
    return `${window.location.origin}/register?ref=${encodeURIComponent(summary.referral_code)}`;
  }, [summary]);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="account-page">
      <div className="page-title">
        <div>
          <p className="eyebrow">Приглашайте друзей</p>
          <h1>Реферальная программа</h1>
        </div>
      </div>

      {error ? (
        <div className="notice danger">{error}</div>
      ) : summary ? (
        <>
          <Card className="referral-hero-card">
            <div className="referral-hero-icon">
              <Share2 />
            </div>
            <div>
              <h2>Ваша персональная ссылка</h2>
              <p>
                Отправьте её другу. Персональный код уже указан в ссылке
                регистрации.
              </p>
              <div className="referral-link-row">
                <code>{referralLink}</code>
                <CopyButton value={referralLink} label="Скопировать ссылку" />
              </div>
              <div className="referral-code-row">
                <span>Код: <strong>{summary.referral_code}</strong></span>
                <CopyButton value={summary.referral_code} label="Копировать код" />
              </div>
            </div>
          </Card>

          <div className="dashboard-grid referral-metrics">
            <Card className="metric-card">
              <UsersRound />
              <span>Приглашено</span>
              <strong>{summary.invited_count}</strong>
            </Card>
            <Card className="metric-card">
              <CheckCircle2 />
              <span>Активировали программу</span>
              <strong>{summary.active_invited_count}</strong>
            </Card>
            <Card className="metric-card">
              <Gift />
              <span>Бонусы за активации</span>
              <strong><MoneyValue value={summary.purchase_bonus_earned} /></strong>
            </Card>
            <Card className="metric-card">
              <Sparkles />
              <span>Премиальные бонусы</span>
              <strong><MoneyValue value={summary.reward_bonus_earned} /></strong>
            </Card>
          </div>

          <div className="two-column referral-rules-grid">
            <Card>
              <h2>Как начисляются бонусы</h2>
              <div className="referral-rule-list">
                <div>
                  <span className="referral-rule-icon"><UserPlus /></span>
                  <div>
                    <strong>{summary.purchase_bonus_percent}% от стоимости программы</strong>
                    <p>
                      Вы получаете бонус после того, как приглашённый друг
                      активирует любую клиентскую программу.
                    </p>
                  </div>
                </div>
                <div>
                  <span className="referral-rule-icon"><Sparkles /></span>
                  <div>
                    <strong>
                      +<MoneyValue value={summary.premium_reward_bonus} />
                    </strong>
                    <p>
                      Если друг выбрал премиальную программу, вы дополнительно
                      получаете этот бонус при каждом его вознаграждении.
                    </p>
                  </div>
                </div>
              </div>
            </Card>
            <Card className="referral-total-card">
              <Link2 />
              <span>Всего получено по приглашениям</span>
              <strong><MoneyValue value={summary.total_earned} /></strong>
              <p>Все начисления отражаются в разделе «Операции».</p>
            </Card>
          </div>

          <Card>
            <div className="card-heading">
              <div>
                <h2>Приглашённые пользователи</h2>
                <p className="muted">Показываются только скрытые адреса электронной почты.</p>
              </div>
            </div>
            {summary.members.length ? (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Пользователь</th>
                      <th>Дата регистрации</th>
                      <th>Статус</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.members.map((member, index) => (
                      <tr key={`${member.email}-${member.joined_at}-${index}`}>
                        <td>{member.email}</td>
                        <td>{formatDateOnly(member.joined_at)}</td>
                        <td>
                          <span className={`status status-${member.has_program ? "active" : "waiting"}`}>
                            {member.has_program ? "Программа активирована" : "Ожидает активации"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                title="Пока никого нет"
                text="Поделитесь своей ссылкой, чтобы начать получать реферальные бонусы."
              />
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
