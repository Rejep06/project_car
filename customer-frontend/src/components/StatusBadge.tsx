const labels: Record<string, string> = {
  waiting: "Ожидает оплату",
  detected: "Обнаружен",
  credited: "Зачислен",
  expired: "Основной срок истёк",
  manual_review: "Требует уточнения",
  cancelled: "Отменён",
  active: "Активна",
  paid: "Выплачено",
  pending: "Ожидает",
  processing: "Обрабатывается",
  failed: "Ошибка",
  pending_review: "Ожидает проверки",
  approved: "Подтверждён",
  sent: "Отправлен",
  completed: "Завершён",
  rejected: "Отклонён",
  open: "Открыто",
  in_review: "На проверке",
  waiting_user: "Ожидает пользователя",
  resolved: "Решено",
  closed: "Закрыто",
  published: "Опубликовано",
  draft: "Черновик",
  archived: "В архиве",
  deposit_credit: "Пополнение",
  program_purchase: "Активация программы",
  referral_purchase_bonus: "Бонус за приглашение",
  referral_reward_bonus: "Премиальный бонус",
  reward_credit: "Вознаграждение",
  withdrawal_hold: "Блокировка вывода",
  withdrawal_complete: "Завершение вывода",
  withdrawal_refund: "Возврат вывода",
  admin_adjustment: "Корректировка",
  lottery_ticket_purchase: "Покупка лотерейных билетов",
  lottery_prize_credit: "Денежный приз",
  lottery_ticket_refund: "Возврат за билет",
  awaiting_confirmation: "Ожидает подтверждения",
  confirmed: "Подтверждено",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`status status-${status}`}>
      {labels[status] ?? status}
    </span>
  );
}
