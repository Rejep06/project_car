# Automotive Admin Frontend

Отдельная административная React-панель. Это самостоятельная сборка на порту 3001, не маршрут `/admin` клиентского сайта.

## Назначение

Панель позволяет администратору:

- управлять программами подписок;
- просматривать пользователей и их кошельки;
- замораживать и размораживать пользователей;
- выполнять журналируемую корректировку через backend `WalletService`;
- обрабатывать нераспознанные пополнения;
- рассматривать ручные выводы;
- отвечать на обращения и проверять TxID;
- управлять новостями;
- просматривать неизменяемый AuditLog.

Админ-панель не обращается к Binance напрямую. Все действия проходят через FastAPI и повторно проверяются backend.

## Стек и архитектура

```text
page → component → API function → FastAPI
```

Используются React, Vite, TypeScript, React Router, native `fetch`, Context API для auth, Lucide, обычный CSS, Vitest и React Testing Library.

```text
src/
├── api/          # фактические admin endpoints
├── auth/         # токены, роль admin, AdminRoute
├── components/   # layout, таблицы, формы, modal, status
├── pages/        # рабочие разделы
├── styles/       # светлая административная тема
├── test/         # 16 обязательных сценариев
└── utils/        # деньги, даты, labels
```

Полная карта API: [BACKEND_API_MAP.md](BACKEND_API_MAP.md).

## Запуск

```bash
cp .env.example .env
npm ci
npm run dev
```

Админ-панель:

```text
http://localhost:3001
```

Backend:

```text
http://localhost:8000
```

## `.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_ADMIN_APP_NAME=Панель управления
```

Никаких Binance/JWT/DB-секретов в frontend нет.

## Вход и роли

После login панель вызывает `GET /users/me` и требует:

```text
role = admin
```

Обычная пользовательская учётная запись получает понятную ошибку, её локальная сессия очищается. React-проверка является только UI-барьером: каждый `/admin/...` endpoint также защищён FastAPI dependency `get_current_admin`.

Access token хранится в памяти, refresh token — в `localStorage` в соответствии с текущим backend-контрактом. При 401 выполняется одна refresh-попытка и один повтор запроса.

## Dashboard

Отдельного агрегированного backend endpoint нет. Dashboard:

- вызывает только первые страницы существующих списков;
- берёт значения `total`;
- не загружает все записи;
- предоставляет быстрые ссылки.

## Управление подписками

Форма разделена на:

- основную информацию;
- стоимость и срок;
- вознаграждения;
- описание и изображение;
- предварительный просмотр.

Денежные поля остаются строками. Категории `game/application` являются техническим ограничением текущего backend и в админ-форме показаны нейтральными названиями «Основная» и «Расширенная».

## Пользователи

Список backend уже возвращает available и locked balance, поэтому нет запроса на каждую строку.

Страница пользователя показывает профиль и кошелёк. Доступны:

- freeze/unfreeze;
- специальный balance-adjustment endpoint с `Idempotency-Key`.

Кнопки прямого присваивания баланса нет. Backend создаёт WalletTransaction и AuditLog.

Текущий API не предоставляет admin subresources по одному пользователю для всех его подписок, операций и заявок. Панель честно указывает это вместо вымышленных запросов.

## Нераспознанные пополнения

Список показывает TxID, Binance deposit ID, сумму, сеть, причину и статус. Поиск и фильтры работают на текущей странице, поскольку серверные query-фильтры отсутствуют.

Перед ручным зачислением открывается ConfirmDialog с:

- UUID пользователя;
- фактической суммой;
- TxID.

Endpoint `/assign` повторно проверяет депозит и использует backend idempotency. Повторная отправка не должна увеличить баланс второй раз.

## Ручные выводы

Панель показывает только допустимые для текущего статуса действия:

```text
pending_review → approve или reject
approved       → mark-sent
sent           → complete
```

`mark-sent` требует TxID и фактическую комиссию. Backend не содержит Binance withdrawal API; администратор сначала выполняет реальный перевод вручную.

## Поддержка

В обращении доступны:

- пользователь и email;
- связанная заявка;
- ожидаемая и фактическая сумма;
- TxID и Binance data;
- предупреждение о конфликте;
- сообщения;
- защищённые вложения;
- статусы;
- ручное разрешение депозита.

Панель не раскрывает данные другого владельца TxID клиенту.

## Новости

Поддерживаются:

- создание черновика;
- чтение существующего черновика по UUID;
- изменение;
- публикация;
- архивирование;
- простой текстовый preview.

Тяжёлого визуального Markdown-редактора нет.

## Audit log

Таблица показывает администратора, действие, объект, дату, IP, old/new JSON. Редактирование отсутствует.

## Деньги

`src/utils/money.ts` использует `BigInt` и шесть atomic digits. `parseFloat` и преобразование денежных строк через JavaScript `number` не используются.

## Маршруты

```text
/login
/
/plans
/plans/new
/plans/:id
/users
/users/:id
/deposits
/deposits/:id
/withdrawals
/withdrawals/:id
/support
/support/:id
/posts
/posts/new
/posts/:id
/audit
```

## Проверки

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm audit
```

16 тестов покрывают вход, role guard, программы, депозиты, ConfirmDialog, выводы, обязательный TxID, поддержку, новости, AuditLog и отображение API-ошибок.

## Production

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  --build-arg VITE_ADMIN_APP_NAME="Панель управления" \
  -t automotive-admin-frontend .

docker run --rm -p 3001:80 automotive-admin-frontend
```

Nginx настроен на React Router fallback.

## С чего начать изучение

1. `src/main.tsx`.
2. `src/App.tsx`.
3. `src/components/AdminLayout.tsx`.
4. `src/pages/`.
5. `src/api/client.ts`.
6. `src/auth/AuthContext.tsx` и `AdminRoute.tsx`.
7. `src/styles/admin.css`.

## Известные ограничения

- нет отдельного dashboard endpoint;
- серверные фильтры для admin lists отсутствуют;
- нет KYC API;
- нет admin user subresources;
- refresh token пока хранится в `localStorage`;
- browser-интеграция с живым PostgreSQL/Binance зависит от настроенного backend окружения.
