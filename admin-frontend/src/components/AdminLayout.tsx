import {
  ClipboardList,
  CreditCard,
  FileText,
  Gauge,
  Headphones,
  LogOut,
  Menu,
  TicketCheck,
  Newspaper,
  Users,
  WalletCards,
  Landmark,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { getUnreadSupportCount } from "../api/support";
import { useAuth } from "../auth/AuthContext";
import { brandLogoUrl } from "../config/assets";
import { useUnreadCount } from "../hooks/useUnreadCount";
import { SUPPORT_READ_EVENT } from "../utils/unreadEvents";
const items = [
  ["/", "Обзор", Gauge],
  ["/plans", "Программы", CreditCard],
  ["/lotteries", "Лотереи", TicketCheck],
  ["/users", "Пользователи", Users],
  ["/deposits", "Пополнения", WalletCards],
  ["/deposit-wallets", "Адреса пополнения", Landmark],
  ["/withdrawals", "Выводы", ClipboardList],
  ["/support", "Поддержка", Headphones],
  ["/posts", "Публикации", Newspaper],
  ["/audit", "Аудит", FileText],
] as const;
export function AdminLayout() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const supportCount = useUnreadCount(user?.id, location.pathname, getUnreadSupportCount, SUPPORT_READ_EVENT);
  async function exit() {
    await logout();
    navigate("/login", { replace: true });
  }
  return (
    <div className="admin-shell">
      <button
        className="mobile-menu"
        type="button"
        aria-label="Открыть меню"
        onClick={() => setOpen(true)}
      >
        <Menu />
        {supportCount > 0 && <span className="mobile-unread-dot" aria-label="Есть непрочитанные сообщения" />}
      </button>
      {open && (
        <button
          className="sidebar-overlay"
          aria-label="Закрыть меню"
          onClick={() => setOpen(false)}
        />
      )}
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand">
          <img className="brand-logo" src={brandLogoUrl} alt="" width="42" height="42" />
          <div>
            <strong>
              {import.meta.env.VITE_ADMIN_APP_NAME || "Панель управления"}
            </strong>
            <small>Automotive Company</small>
          </div>
          <button
            className="sidebar-close"
            type="button"
            aria-label="Закрыть"
            onClick={() => setOpen(false)}
          >
            <X />
          </button>
        </div>
        <nav aria-label="Разделы панели управления">
          {items.map(([to, text, Icon]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => [isActive && "active", to === "/support" && supportCount > 0 && "has-unread"].filter(Boolean).join(" ")}
              onClick={() => setOpen(false)}
            >
              <Icon />
              <span>{text}</span>
              {to === "/support" && supportCount > 0 && <span className="nav-count" aria-label={`Непрочитанных сообщений поддержки: ${supportCount}`} aria-live="polite">{supportCount > 99 ? "99+" : supportCount}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-user">
          <div>
            <small>Текущий администратор</small>
            <strong>{user?.email}</strong>
          </div>
          <button type="button" onClick={exit}>
            <LogOut />
            <span>Выйти</span>
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
}
