import {
  Building2,
  CarFront,
  CircleHelp,
  LogIn,
  LogOut,
  Menu,
  Newspaper,
  Route,
  Ticket,
  UserRound,
  WalletCards,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { brandLogoUrl } from "../config/assets";
import { content } from "../config/content";
import { Button } from "./Button";

const publicLinks = [
  { to: "/news", label: "Публикации", icon: Newspaper },
  { to: "/about", label: "О компании", icon: Building2 },
  { to: "/plans", label: "Программы", icon: CarFront },
  { to: "/lotteries", label: "Лотереи", icon: Ticket },
  { to: "/how-it-works", label: "Как это работает", icon: Route },
  { to: "/faq", label: "Вопросы", icon: CircleHelp },
] as const;

export function PublicLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setOpen(false), [location.pathname]);

  useEffect(() => {
    if (!open) return undefined;

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    function closeOnResize() {
      if (window.innerWidth > 1260) setOpen(false);
    }

    window.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeOnResize);

    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeOnResize);
    };
  }, [open]);

  async function signOut() {
    setOpen(false);
    await logout();
  }

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link className="brand header-brand" to="/" aria-label="На главную">
            <img
              className="brand-logo"
              src={brandLogoUrl}
              alt=""
              width="42"
              height="42"
            />
            <span className="brand-name">{content.companyName}</span>
          </Link>

          <nav className="main-nav desktop-public-nav" aria-label="Основная навигация">
            {publicLinks.map(({ to, label }) => (
              <NavLink key={to} to={to}>
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="header-actions desktop-header-actions">
            {user ? (
              <>
                <Link className="button button-secondary header-action" to="/account/wallet">
                  <WalletCards size={17} aria-hidden="true" />
                  Баланс
                </Link>
                <Link className="button button-primary header-action" to="/account">
                  <UserRound size={17} aria-hidden="true" />
                  Личный кабинет
                </Link>
                <Button
                  className="header-logout-action"
                  variant="ghost"
                  onClick={() => void signOut()}
                >
                  <LogOut size={17} aria-hidden="true" />
                  Выйти
                </Button>
              </>
            ) : (
              <>
                <Link className="header-login-link" to="/login">
                  <LogIn size={17} aria-hidden="true" />
                  Войти
                </Link>
                <Link className="button button-primary header-action" to="/register">
                  <UserRound size={17} aria-hidden="true" />
                  Создать аккаунт
                </Link>
              </>
            )}
          </div>

          <button
            className="mobile-menu-button"
            type="button"
            aria-label={open ? "Закрыть меню" : "Открыть меню"}
            aria-expanded={open}
            aria-controls="mobile-public-menu"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X aria-hidden="true" /> : <Menu aria-hidden="true" />}
          </button>

          <div
            id="mobile-public-menu"
            className={`mobile-public-menu ${open ? "open" : ""}`}
          >
            <div className="mobile-menu-heading">
              <span>Навигация</span>
              <small>Выберите нужный раздел</small>
            </div>

            <nav aria-label="Мобильная навигация">
              {publicLinks.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to}>
                  <span className="mobile-nav-icon" aria-hidden="true">
                    <Icon size={19} />
                  </span>
                  <span>{label}</span>
                </NavLink>
              ))}
            </nav>

            <div className="mobile-public-actions">
              {user ? (
                <>
                  <Link className="mobile-account-link" to="/account/wallet">
                    <WalletCards size={19} aria-hidden="true" /> Баланс
                  </Link>
                  <Link className="mobile-account-link primary" to="/account">
                    <UserRound size={19} aria-hidden="true" /> Личный кабинет
                  </Link>
                  <button type="button" onClick={() => void signOut()}>
                    <LogOut size={19} aria-hidden="true" /> Выйти
                  </button>
                </>
              ) : (
                <>
                  <Link className="mobile-account-link" to="/login">
                    <LogIn size={19} aria-hidden="true" /> Войти
                  </Link>
                  <Link className="mobile-account-link primary" to="/register">
                    <UserRound size={19} aria-hidden="true" /> Создать аккаунт
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <main>
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <div className="brand brand-light">
              <img
                className="brand-logo"
                src={brandLogoUrl}
                alt=""
                width="42"
                height="42"
              />
              <span>{content.companyName}</span>
            </div>
            <p>
              Автомобильная компания и клиентские программы с понятными
              условиями. Работаем с 2023 года.
            </p>
          </div>
          <div>
            <h3>Разделы</h3>
            <Link to="/news">Публикации</Link>
            <Link to="/plans">Программы</Link>
            <Link to="/lotteries">Лотереи</Link>
            <Link to="/faq">FAQ</Link>
          </div>
          <div>
            <h3>Документы</h3>
            <Link to="/terms">Условия</Link>
            <Link to="/privacy">Конфиденциальность</Link>
            <Link to="/program-rules">Правила программ и лотерей</Link>
            <Link to="/personal-data-consent">Персональные данные</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
