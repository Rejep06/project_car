import { Bell, CheckCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../../api/notifications";
import type { UserNotification } from "../../api/types";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { LoadingSpinner } from "../../components/LoadingSpinner";
import { formatDate } from "../../utils/date";

export function NotificationsPage() {
  const [items, setItems] = useState<UserNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    const data = await listNotifications(1, 100);
    setItems(data.items);
  }

  useEffect(() => {
    load().catch((reason: Error) => setError(reason.message)).finally(() => setLoading(false));
  }, []);

  async function read(item: UserNotification) {
    if (!item.is_read) {
      await markNotificationRead(item.id);
      await load();
    }
  }

  async function readAll() {
    await markAllNotificationsRead();
    await load();
  }

  return (
    <div className="account-page">
      <div className="page-title">
        <div><p className="eyebrow">Сообщения</p><h1>Уведомления</h1></div>
        {items.some((item) => !item.is_read) && <Button variant="secondary" onClick={() => void readAll()}><CheckCheck size={18} /> Прочитать все</Button>}
      </div>
      {loading ? <LoadingSpinner /> : error ? <div className="notice danger">{error}</div> : items.length ? (
        <div className="notification-list">
          {items.map((item) => (
            <Card key={item.id} className={item.is_read ? "notification-card" : "notification-card unread"}>
              <Bell size={20} />
              <div>
                <h2>{item.title}</h2>
                <p>{item.message}</p>
                <small>{formatDate(item.created_at)}</small>
                <div className="notification-actions">
                  {item.action_url && (item.action_url.startsWith("http") ? <a href={item.action_url} target="_blank" rel="noreferrer">Открыть</a> : <Link to={item.action_url}>Открыть</Link>)}
                  {!item.is_read && <button type="button" onClick={() => void read(item)}>Отметить прочитанным</button>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : <EmptyState title="Уведомлений нет" text="Здесь появятся важные сообщения и результаты лотерей." />}
    </div>
  );
}
