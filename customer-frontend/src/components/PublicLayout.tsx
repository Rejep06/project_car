import { CarFront, Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { content } from "../config/content";
import { Button } from "./Button";

export function PublicLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="container header-inner">
          <Link className="brand" to="/" aria-label="На главную">
            <span className="brand-mark">
              <CarFront />
            </span>
            <span>{content.companyName}</span>
          </Link>
          <button
            className="mobile-menu-button"
            type="button"
            aria-label="Открыть меню"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
          <nav
            className={`main-nav ${open ? "open" : ""}`}
            aria-label="Основная навигация"
            onClick={() => setOpen(false)}
          >
            <NavLink to="/about">О компании</NavLink>
            <NavLink to="/plans">Программы</NavLink>
            <NavLink to="/how-it-works">Как это работает</NavLink>
            <NavLink to="/news">Новости</NavLink>
            <NavLink to="/faq">Вопросы</NavLink>
          </nav>
          <div className="header-actions">
            {user ? (
              <>
                <Link className="button button-secondary" to="/account/wallet">
                  Баланс
                </Link>
                <Link className="button button-primary" to="/account">
                  Личный кабинет
                </Link>
                <Button variant="ghost" onClick={() => void logout()}>
                  Выйти
                </Button>
              </>
            ) : (
              <>
                <Link className="text-link" to="/login">
                  Войти
                </Link>
                <Link className="button button-primary" to="/register">
                  Создать аккаунт
                </Link>
              </>
            )}
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
              <span className="brand-mark">
                <CarFront />
              </span>
              <span>{content.companyName}</span>
            </div>
            <p>
              Автомобильная компания и отдельная клиентская программа подписок.
            </p>
          </div>
          <div>
            <h3>Разделы</h3>
            <Link to="/plans">Программы</Link>
            <Link to="/news">Новости</Link>
            <Link to="/faq">FAQ</Link>
          </div>
          <div>
            <h3>Документы</h3>
            <Link to="/terms">Условия</Link>
            <Link to="/privacy">Конфиденциальность</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
