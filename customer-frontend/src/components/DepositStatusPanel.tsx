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
  const validUntil = new Date(invoice.amount_reserved_until);
  const mainExpired = now > expires;
  const validityExpired = now > validUntil;

  if (invoice.status === "credited") {
    return (
      <div className="notice success">
        <h3>Платёж успешно зачислен</h3>
        <p>
          Получено: <MoneyValue value={invoice.received_amount ?? invoice.expected_amount} />
        </p>
      </div>
    );
  }
  if (validityExpired) {
    return (
      <div className="notice danger">
        <h3>Срок действия реквизитов завершён</h3>
        <p>Не отправляйте перевод по этой заявке. Создайте новую заявку или обратитесь в поддержку, если платёж уже выполнен.</p>
      </div>
    );
  }
  if (mainExpired) {
    return (
      <div className="notice warning">
        <h3>Основной срок заявки завершён</h3>
        <p>
          Если перевод уже выполнен, дождитесь обновления статуса. Реквизиты действительны до {formatDate(invoice.amount_reserved_until)}.
        </p>
      </div>
    );
  }
  return (
    <div className="notice info">
      <h3>Заявка ожидает оплату</h3>
      <p>Переведите точную сумму до {formatDate(invoice.expires_at)}.</p>
      <StatusBadge status={invoice.status} />
    </div>
  );
}
