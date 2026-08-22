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
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { brandLogoUrl } from "../config/assets";
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
        <nav>
          {items.map(([to, text, Icon]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
            >
              <Icon />
              <span>{text}</span>
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
