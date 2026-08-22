import { RefreshCw } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { DepositInvoice } from "../../api/types";
import { getDeposit } from "../../api/wallet";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { CopyButton } from "../../components/CopyButton";
import { DepositStatusPanel } from "../../components/DepositStatusPanel";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { MoneyValue } from "../../components/MoneyValue";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../utils/date";

export function DepositDetailsPage() {
  const { id = "" } = useParams();
  const [invoice, setInvoice] = useState<DepositInvoice | null>(null);
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      setInvoice(await getDeposit(id));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить заявку");
    } finally {
      setRefreshing(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  if (error) return <div className="notice danger">{error}</div>;
  if (!invoice) return <LoadingSpinner />;
  const supportUrl = `/account/support?invoiceId=${encodeURIComponent(invoice.id)}&expected=${encodeURIComponent(invoice.expected_amount)}`;
  return (
    <div className="account-page">
      <Link to="/account/deposits">← Все пополнения</Link>
      <div className="page-title">
        <div>
          <p className="eyebrow">Заявка на пополнение</p>
          <h1>
            <MoneyValue value={invoice.expected_amount} />
          </h1>
        </div>
        <div className="page-actions">
          <StatusBadge status={invoice.status} />
          <Button
            variant="secondary"
            loading={refreshing}
            onClick={() => void load()}
          >
            <RefreshCw size={16} /> Обновить
          </Button>
        </div>
      </div>
      <DepositStatusPanel invoice={invoice} />
      <div className="deposit-grid">
        <Card>
          <h2>Реквизиты перевода</h2>
          <dl className="detail-list">
            <div>
              <dt>Кошелёк</dt>
              <dd>{invoice.wallet_name}</dd>
            </div>
            <div>
              <dt>Монета</dt>
              <dd>{invoice.asset}</dd>
            </div>
            <div>
              <dt>Сеть</dt>
              <dd>{invoice.network}</dd>
            </div>
            <div>
              <dt>Адрес</dt>
              <dd className="break-all">
                {invoice.address}
                <CopyButton value={invoice.address} />
              </dd>
            </div>
            <div>
              <dt>Желаемая сумма</dt>
              <dd>
                <MoneyValue value={invoice.requested_amount} />
              </dd>
            </div>
            <div>
              <dt>Точная сумма</dt>
              <dd>
                <MoneyValue value={invoice.expected_amount} />
                <CopyButton value={invoice.expected_amount} />
              </dd>
            </div>
            <div>
              <dt>Основной срок</dt>
              <dd>{formatDate(invoice.expires_at)}</dd>
            </div>
            <div>
              <dt>Реквизиты действительны до</dt>
              <dd>{formatDate(invoice.amount_reserved_until)}</dd>
            </div>
          </dl>
        </Card>
        <Card className="qr-card">
          <h2>QR-код адреса</h2>
          <QRCodeSVG value={invoice.address} size={190} marginSize={2} />
          <p className="small muted">
            QR содержит только адрес. Точную сумму укажите вручную.
          </p>
        </Card>
      </div>
      <div className="notice warning">
        <strong>
          Отправьте ровно указанную сумму через сеть {invoice.network}.
        </strong>
        <p>
          Проверьте адрес, сеть и точную сумму перед подтверждением. Не отправляйте {invoice.asset} через другую сеть.
        </p>
      </div>
      <div className="page-actions">
        <Link className="button button-secondary" to="/account/deposits">
          Создать новую заявку
        </Link>
        <Link className="button button-primary" to={supportUrl}>
          Сообщить о проблеме
        </Link>
      </div>
    </div>
  );
}
