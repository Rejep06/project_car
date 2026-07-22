# Automotive Customer Frontend

Отдельное клиентское React-приложение для автомобильной компании и её программы подписок. Оно не содержит административных маршрутов и не обращается к Binance напрямую.

## Что реализовано

- публичный автомобильный сайт;
- каталог и страницы программ подписки;
- регистрация, вход, logout, refresh и восстановление сессии;
- покупка подписки с `Idempotency-Key`;
- личный кабинет;
- available и locked balance;
- история WalletTransaction;
- графики RewardPayout внутри купленной подписки;
- создание и просмотр пополнений USDT TRC20;
- отображение основного срока 30 минут и периода распознавания 24 часа;
- QR-код, копирование адреса и точной суммы;
- ручные выводы;
- обращения с TxID и вложениями;
- публичные новости;
- адаптивность от 320 px;
- loading, empty, error и disabled states;
- Vitest + React Testing Library.

## Стек

- React;
- Vite;
- TypeScript;
- React Router;
- native `fetch`;
- Context API только для авторизации;
- уведомления через простой browser event и `ToastRegion`;
- обычный CSS;
- Lucide React;
- `qrcode.react`;
- Vitest и React Testing Library.

Redux, Tailwind, Material UI, GraphQL и универсальный SDK не используются.

## Архитектура

```text
page → component → API function → FastAPI
```

```text
src/
├── api/          # запросы и TypeScript-типы фактического API
├── auth/         # токены, AuthContext, ProtectedRoute
├── components/   # небольшие визуальные компоненты
├── config/       # редактируемые тексты компании
├── pages/        # публичные страницы и личный кабинет
├── styles/       # CSS по назначению
├── test/         # 18 UI/API-mock сценариев
└── utils/        # money/date/reward helpers
```

Полная карта backend находится в [BACKEND_API_MAP.md](BACKEND_API_MAP.md).

## Запуск

Требуется Node.js 20.19+ или 22.12+.

```bash
cp .env.example .env
npm ci
npm run dev
```

Сайт:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

## `.env`

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Automotive Club
```

В frontend разрешены только публичные Vite-переменные. Здесь не должно быть:

- Binance API Key или Secret;
- JWT Secret;
- DATABASE_URL;
- пароля PostgreSQL;
- backend `.env`.

## Авторизация

Код расположен в `src/auth/` и `src/api/client.ts`.

- access token хранится только в памяти вкладки;
- refresh token хранится в `localStorage`, поскольку текущий backend возвращает его JSON-телом, а не HttpOnly cookie;
- при `401` выполняется одна попытка refresh;
- исходный запрос повторяется один раз;
- при неудаче токены удаляются;
- бесконечного refresh loop нет.

Для production предпочтительнее изменить backend на защищённую HttpOnly Secure SameSite cookie для refresh token.

## Работа с деньгами

Все суммы остаются строками. Финансовые вычисления находятся в `src/utils/money.ts` и выполняются через `BigInt` в масштабе:

```text
1 USDT = 1 000 000 atomic units
```

Для баланса, цены и комиссии не используются `parseFloat` или `Number(value)`.

## Подписки

Frontend получает из backend:

- стоимость;
- срок доступа;
- сумму одного вознаграждения;
- частоту;
- период начислений;
- статус.

Технические категории backend `game/application` не показываются клиенту. Каталог не создаёт собственные финансовые условия.

При покупке:

1. проверяется авторизация;
2. загружается текущий кошелёк;
3. при недостаточном балансе показывается недостающая сумма;
4. открывается подтверждение;
5. создаётся стабильный UUID для `Idempotency-Key`;
6. повторное нажатие блокируется;
7. после успеха открывается купленная подписка.

## Пополнение: 30 минут и 24 часа

Backend возвращает два разных срока:

```text
expires_at
amount_reserved_until
```

- первые 30 минут — основной срок оплаты;
- после 30 минут заявка показывается как истёкшая, но точная сумма остаётся закреплена;
- точный платёж с фактическим временем до конца 24 часов может быть зачислен автоматически;
- для позднего зачисления отображается `credited_after_expiration`;
- после 24 часов интерфейс предлагает создать обращение с TxID;
- неправильная сумма не зачисляется автоматически.

Страница заявки показывает адрес, QR-код, точную сумму, оба срока и понятные предупреждения.

## Вывод

Вывод полностью ручной:

1. пользователь создаёт заявку;
2. сумма с комиссией переходит в `locked_balance`;
3. администратор проверяет заявку;
4. администратор вручную отправляет USDT;
5. после `mark-sent` пользователь видит TxID;
6. после `complete` locked balance уменьшается.

Frontend не содержит Binance SDK и не имеет API-ключей.

## Поддержка и TxID

Пользователь может создать обращение, указать:

- категорию;
- связанную заявку;
- TxID;
- фактическую сумму;
- описание;
- до трёх вложений по 5 MB.

Текущий `TicketCreate` не имеет отдельного поля фактической суммы. Поэтому интерфейс явно сохраняет её в первом сообщении. Это ограничение отмечено в API map.

Вложения скачиваются защищённым fetch-запросом с авторизацией. Реальный путь сервера не отображается.

## Контент и визуальный стиль

Основные редактируемые тексты находятся в:

```text
src/config/content.ts
```

Там меняются:

- название и описание компании;
- год начала работы;
- число автомобилей в месяц;
- число партнёров;
- FAQ;
- юридическое уточнение.

Формулировки «инвестиция», «вклад», «гарантированная прибыль», «пассивный доход без риска», «заработок на автомобилях», «гарантированный процент» и «умножение капитала» используются только в уточнении, что они **не описывают** продукт. Финансовые обещания frontend не придумывает.

Цвета находятся в `src/styles/base.css` в CSS variables. Логотип сейчас текстовый; его можно заменить в `PublicLayout.tsx`. Изображения планов и новостей приходят из backend.

## Маршруты

Публичные:

```text
/
/plans
/plans/:slug
/news
/news/:slug
/about
/how-it-works
/faq
/login
/register
/terms
/privacy
```

Личный кабинет:

```text
/account
/account/wallet
/account/deposits
/account/deposits/:id
/account/withdrawals
/account/subscriptions
/account/subscriptions/:id
/account/rewards
/account/transactions
/account/support
/account/support/:id
/account/profile
```

## Проверки

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm audit
```

В проекте 18 обязательных тестов. Реальные Binance-запросы не выполняются; API-интеграция в frontend-тестах проверяется через mock `fetch`.

## Production build

```bash
npm run build
npm run preview
```

Nginx Docker image:

```bash
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8000/api/v1 \
  --build-arg VITE_APP_NAME="Automotive Club" \
  -t automotive-customer-frontend .

docker run --rm -p 3000:80 automotive-customer-frontend
```

`nginx.conf` содержит:

```nginx
try_files $uri $uri/ /index.html;
```

Поэтому обновление страницы на вложенном React Router route работает.

## С чего начать изучение

1. `src/main.tsx` — подключение Router, Auth и Toast.
2. `src/App.tsx` — все маршруты.
3. `src/pages/` — конкретные экраны.
4. `src/api/client.ts` — base URL, JWT, refresh, JSON, multipart и ошибки.
5. `src/auth/` — восстановление сессии и защита маршрутов.
6. `src/styles/` — цвета, компоненты и адаптивность.

## Известные ограничения

- refresh token хранится в `localStorage` из-за фактического контракта backend;
- отдельного endpoint для агрегированной истории reward payouts нет;
- фактическая сумма проблемного пополнения сохраняется текстом сообщения;
- маркетинговые страницы `/terms` и `/privacy` являются редактируемыми шаблонами и требуют юридической проверки;
- изображения задаются URL, отдельной загрузки обложек backend не предоставляет.
