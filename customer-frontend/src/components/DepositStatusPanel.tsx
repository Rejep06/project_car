import type { DepositInvoice } from "../api/types";
import { formatDate } from "../utils/date";
import { MoneyValue } from "./MoneyValue";
import { StatusBadge } from "./StatusBadge";

export function DepositStatusPanel({
  invoice,
  now = new Date(),
}: {
  invoice: DepositInvoice;
  now?: Date;
}) {
  const expires = new Date(invoice.expires_at);
  const reserved = new Date(invoice.amount_reserved_until);
  const mainExpired = now > expires;
  const reservationExpired = now > reserved;

  if (invoice.status === "credited") {
    return (
      <div className="notice success">
        <h3>Платёж успешно зачислен</h3>
        <p>
          Получено:{" "}
          <MoneyValue
            value={invoice.received_amount ?? invoice.expected_amount}
          />
        </p>
        {invoice.credited_after_expiration && (
          <p>
            Платёж поступил после основного срока заявки, но был автоматически
            зачислен.
          </p>
        )}
      </div>
    );
  }
  if (reservationExpired) {
    return (
      <div className="notice danger">
        <h3>Период автоматического распознавания завершён</h3>
        <p>Если деньги уже отправлены, создайте обращение и укажите TxID.</p>
      </div>
    );
  }
  if (mainExpired) {
    return (
      <div className="notice warning">
        <h3>Ожидаем возможный поздний платёж</h3>
        <p>
          Основной срок заявки истёк. Если точная сумма уже отправлена, система
          продолжит проверку до {formatDate(invoice.amount_reserved_until)}.
        </p>
        <p>Не отправляйте деньги после окончания 24 часов.</p>
      </div>
    );
  }
  return (
    <div className="notice info">
      <h3>Основной срок оплаты</h3>
      <p>Отправьте точную сумму до {formatDate(invoice.expires_at)}.</p>
      <StatusBadge status={invoice.status} />
    </div>
  );
}
