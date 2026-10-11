import { Bell, CheckCheck } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
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
import { useLiveRefresh } from "../../hooks/useLiveRefresh";
import { formatDate } from "../../utils/date";

export function NotificationsPage() {
  const [items, setItems] = useState<UserNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pending, setPending] = useState("");
  const loadVersion = useRef(0);
  const mounted = useRef(true);

  const load = useCallback(async () => {
    const version = ++loadVersion.current;
    try {
      const data = await listNotifications(1, 100);
      if (version === loadVersion.current) {
        setItems(data.items);
        setError("");
      }
    } catch (reason) {
      if (version === loadVersion.current) setError(reason instanceof Error ? reason.message : "Не удалось загрузить уведомления");
    } finally {
      if (version === loadVersion.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void load();
    return () => { mounted.current = false; loadVersion.current += 1; };
  }, [load]);
  useLiveRefresh(load);

  async function read(item: UserNotification) {
    if (item.is_read || pending) return;
    setPending(item.id);
    try {
      const updated = await markNotificationRead(item.id);
      if (!mounted.current) return;
      setItems((current) => current.map((entry) => entry.id === updated.id ? updated : entry));
      await load();
    } catch (reason) {
      if (mounted.current) setError(reason instanceof Error ? reason.message : "Не удалось отметить уведомление");
    } finally {
      if (mounted.current) setPending("");
    }
  }

  async function readAll() {
    if (pending) return;
    setPending("all");
    try {
      await markAllNotificationsRead();
      if (!mounted.current) return;
      setItems((current) => current.map((item) => ({ ...item, is_read: true })));
      await load();
    } catch (reason) {
      if (mounted.current) setError(reason instanceof Error ? reason.message : "Не удалось отметить уведомления");
    } finally {
      if (mounted.current) setPending("");
    }
  }

  return (
    <div className="account-page">
      <div className="page-title">
        <div><p className="eyebrow">Сообщения</p><h1>Уведомления</h1></div>
        {items.some((item) => !item.is_read) && <Button variant="secondary" disabled={Boolean(pending)} loading={pending === "all"} onClick={() => void readAll()}><CheckCheck size={18} /> Прочитать все</Button>}
      </div>
      {error && <div className="notice danger" role="alert">{error}</div>}
      {loading ? <LoadingSpinner /> : items.length ? (
        <div className="notification-list">
          {items.map((item) => (
            <Card key={item.id} className={item.is_read ? "notification-card" : "notification-card unread"}>
              <Bell size={20} />
              <div>
                <h2>{item.title}</h2>
                <p>{item.message}</p>
                <small>{formatDate(item.created_at)}</small>
                <div className="notification-actions">
                  {item.action_url && (item.action_url.startsWith("http") ? <a href={item.action_url} target="_blank" rel="noreferrer" onClick={() => void read(item)}>Открыть</a> : <Link to={item.action_url} onClick={() => void read(item)}>Открыть</Link>)}
                  {!item.is_read && <button type="button" disabled={Boolean(pending)} onClick={() => void read(item)}>Отметить прочитанным</button>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : <EmptyState title="Уведомлений нет" text="Здесь появятся важные сообщения и результаты лотерей." />}
    </div>
  );
}
