# Customer Frontend

Клиентский сайт Automotive Platform на React, TypeScript и Vite.

## Возможности

- публичные страницы компании, программ, публикаций, FAQ и документов;
- регистрация с необязательным реферальным кодом;
- сохранение авторизации после обновления и повторного открытия сайта;
- каталог трёх уровней программ и активация по UUID;
- личный кошелёк и история операций;
- выбор одного из нескольких адресов пополнения;
- заявки на вывод только по средам по времени Алматы;
- вознаграждения и реферальные бонусы;
- персональная реферальная ссылка и статистика приглашённых;
- поддержка с сообщениями и вложениями;
- адаптивное публичное меню и выезжающее меню личного кабинета.

## Запуск

```bash
cp .env.example .env
npm ci
npm run dev
```

Переменная окружения:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Production-проверка:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

## Основные маршруты

```text
/
/news
/news/:slug
/about
/plans
/plans/:id
/how-it-works
/faq
/login
/register
/account
/account/wallet
/account/deposits
/account/deposits/:id
/account/withdrawals
/account/subscriptions
/account/subscriptions/:id
/account/rewards
/account/referrals
/account/transactions
/account/support
/account/support/:id
/account/profile
```

## Авторизация

Access token и refresh token сохраняются локально. После загрузки приложение проверяет текущего пользователя; при истёкшем access token выполняет refresh и сохраняет новую пару. Ошибка сети не удаляет действующую локальную сессию.

## Контент

Основные тексты компании находятся в `src/config/content.ts`. Публичные страницы не показывают пользователю детали backend, фоновых задач или платёжной интеграции.
