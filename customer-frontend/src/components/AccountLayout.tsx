import {
  CreditCard,
  FileText,
  Gift,
  Headphones,
  LayoutDashboard,
  LogOut,
  ReceiptText,
  UserRound,
  WalletCards,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { content } from "../config/content";

const links = [
  ["/account", "Обзор", LayoutDashboard],
  ["/account/wallet", "Кошелёк", WalletCards],
  ["/account/deposits", "Пополнения", CreditCard],
  ["/account/withdrawals", "Выводы", ReceiptText],
  ["/account/subscriptions", "Программы", FileText],
  ["/account/rewards", "Вознаграждения", Gift],
  ["/account/transactions", "Операции", ReceiptText],
  ["/account/support", "Поддержка", Headphones],
  ["/account/profile", "Профиль", UserRound],
] as const;

export function AccountLayout() {
  const { user, logout } = useAuth();
  return (
    <div className="account-shell">
      <aside className="account-sidebar">
        <a className="brand brand-light" href="/">
          <span className="brand-mark">A</span>
          <span>{content.companyName}</span>
        </a>
        <nav>
          {links.map(([to, label, Icon]) => (
            <NavLink key={to} to={to} end={to === "/account"}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-user">
          <p>{user?.email}</p>
          <button type="button" onClick={() => void logout()}>
            <LogOut size={17} /> Выйти
          </button>
        </div>
      </aside>
      <div className="account-content">
        <header className="account-topbar">
          <a href="/">← На сайт</a>
          <span>{user?.email}</span>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
