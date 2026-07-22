const labels: Record<string, string> = {
  waiting: "Ожидает оплату",
  detected: "Обнаружен",
  credited: "Зачислен",
  expired: "Основной срок истёк",
  manual_review: "Ручная проверка",
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
  subscription_purchase: "Покупка программы",
  reward_credit: "Вознаграждение",
  withdrawal_hold: "Блокировка вывода",
  withdrawal_complete: "Завершение вывода",
  withdrawal_refund: "Возврат вывода",
  admin_adjustment: "Корректировка",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`status status-${status}`}>
      {labels[status] ?? status}
    </span>
  );
}
