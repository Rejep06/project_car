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
import { useAuth } from "../auth/AuthContext";
import { brandLogoUrl } from "../config/assets";
import { content } from "../config/content";

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
  const [unreadCount, setUnreadCount] = useState(0);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname]);

  useEffect(() => {
    let active = true;
    getUnreadNotificationCount()
      .then((result) => {
        if (active) setUnreadCount(result.unread_count);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [location.pathname]);

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
          {links.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === "/account"}>
              <Icon size={18} />
              <span>{label}</span>
              {to === "/account/notifications" && unreadCount > 0 ? (
                <span className="nav-count" aria-label={`Непрочитанных уведомлений: ${unreadCount}`}>
                  {unreadCount > 99 ? "99+" : unreadCount}
                </span>
              ) : null}
            </NavLink>
          ))}
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
