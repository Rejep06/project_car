import {
  Bell,
  CreditCard,
  FileText,
  Gift,
  Headphones,
  LayoutDashboard,
  LogOut,
  Menu,
  ReceiptText,
  Share2,
  TicketCheck,
  UserRound,
  WalletCards,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { getUnreadNotificationCount } from "../api/notifications";
import { getUnreadSupportCount } from "../api/support";
import { useAuth } from "../auth/AuthContext";
import { brandLogoUrl } from "../config/assets";
import { content } from "../config/content";
import { useUnreadCount } from "../hooks/useUnreadCount";
import { NOTIFICATIONS_READ_EVENT, SUPPORT_READ_EVENT } from "../utils/unreadEvents";

const links = [
  ["/account", "Обзор", LayoutDashboard],
  ["/account/wallet", "Кошелёк", WalletCards],
  ["/account/deposits", "Пополнения", CreditCard],
  ["/account/withdrawals", "Выводы", ReceiptText],
  ["/account/subscriptions", "Программы", FileText],
  ["/account/rewards", "Вознаграждения", Gift],
  ["/account/lotteries", "Мои лотереи", TicketCheck],
  ["/account/notifications", "Уведомления", Bell],
  ["/account/referrals", "Пригласить друзей", Share2],
  ["/account/transactions", "Операции", ReceiptText],
  ["/account/support", "Поддержка", Headphones],
  ["/account/profile", "Профиль", UserRound],
] as const;

export function AccountLayout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const notificationCount = useUnreadCount(user?.id, location.pathname, getUnreadNotificationCount, NOTIFICATIONS_READ_EVENT);
  const supportCount = useUnreadCount(user?.id, location.pathname, getUnreadSupportCount, SUPPORT_READ_EVENT);

  useEffect(() => setMenuOpen(false), [location.pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [menuOpen]);

  const activeLabel = useMemo(() => {
    const candidates = [...links].sort((a, b) => b[0].length - a[0].length);
    return (
      candidates.find(([to]) =>
        to === "/account"
          ? location.pathname === to
          : location.pathname.startsWith(to),
      )?.[1] || "Личный кабинет"
    );
  }, [location.pathname]);

  async function signOut() {
    setMenuOpen(false);
    await logout();
  }

  return (
    <div className="account-shell">
      <button
        type="button"
        aria-label="Закрыть меню"
        className={`account-sidebar-backdrop ${menuOpen ? "open" : ""}`}
        onClick={() => setMenuOpen(false)}
      />
      <aside className={`account-sidebar ${menuOpen ? "open" : ""}`}>
        <div className="account-sidebar-heading">
          <Link className="brand brand-light" to="/">
            <img
              className="brand-logo"
              src={brandLogoUrl}
              alt=""
              width="42"
              height="42"
            />
            <span>{content.companyName}</span>
          </Link>
          <button
            type="button"
            className="account-sidebar-close"
            aria-label="Закрыть меню"
            onClick={() => setMenuOpen(false)}
          >
            <X size={22} />
          </button>
        </div>
        <nav aria-label="Разделы личного кабинета">
          {links.map(([to, label, Icon]) => {
            const count = to === "/account/notifications" ? notificationCount : to === "/account/support" ? supportCount : 0;
            const countLabel = to === "/account/support" ? "Непрочитанных сообщений поддержки" : "Непрочитанных уведомлений";
            return <NavLink key={to} to={to} end={to === "/account"}
              className={({ isActive }) => [isActive && "active", count > 0 && "has-unread"].filter(Boolean).join(" ")}
            >
              <Icon size={18} />
              <span>{label}</span>
              {count > 0 ? (
                <span className="nav-count" aria-label={`${countLabel}: ${count}`} aria-live="polite">
                  {count > 99 ? "99+" : count}
                </span>
              ) : null}
            </NavLink>;
          })}
        </nav>
        <div className="sidebar-user">
          <p>{user?.email}</p>
          <button type="button" onClick={() => void signOut()}>
            <LogOut size={17} /> Выйти
          </button>
        </div>
      </aside>
      <div className="account-content">
        <header className="account-topbar">
          <div className="account-mobile-navigation">
            <button
              type="button"
              className="account-menu-button"
              aria-label="Открыть меню личного кабинета"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen(true)}
            >
              <Menu size={22} />
              {notificationCount + supportCount > 0 && <span className="mobile-unread-dot" aria-label="Есть непрочитанные сообщения" />}
            </button>
            <strong>{activeLabel}</strong>
          </div>
          <Link className="account-site-link" to="/">
            ← На сайт
          </Link>
          <span className="account-topbar-email">{user?.email}</span>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
