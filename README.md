# Automotive Platform

Полный workspace Automotive Club: публичный автомобильный сайт, личный кабинет, административная панель и FastAPI backend.

## Структура

```text
automotive_platform_workspace/
├── customer-frontend/       # сайт и личный кабинет, порт 3000
├── admin-frontend/          # административная панель, порт 3001
├── backend/                 # FastAPI, PostgreSQL и workers, порт 8000
├── docker-compose.yml
├── docker-compose.server.example.yml
├── .env.example
├── COMPOSE_ENVIRONMENTS.md
├── DEPLOY_DNS_LOTTERY_FIX.md
├── EMAIL_SETUP.md
├── LOTTERY_SETUP.md
├── UPGRADE_EMAIL_LOTTERY.md
├── INFURA_SETUP.md
└── BACKEND_OPENAPI.json
```

## Основная функциональность

### Аккаунт и безопасность

- регистрация только с обязательным подтверждением email;
- повторная отправка письма подтверждения;
- восстановление забытого пароля по email;
- подтверждение нового email при изменении профиля;
- отзыв старых refresh-сессий после смены пароля или email;
- сохранение авторизации после обновления страницы;
- роли `user` и `admin`;
- транзакционная email-очередь и отдельный `email-worker`;
- все PostgreSQL-блокировки `with_for_update` ограничены конкретной таблицей через `of=Model`.

### Юридические согласия

При регистрации пользователь обязан отдельно принять:

- условия использования;
- политику конфиденциальности;
- согласие на обработку персональных данных;
- правила клиентских программ и лотерей;
- подтверждение возраста 18+.

В БД сохраняются тип и версия каждого документа, время согласия, IP и User-Agent.

### Клиентские программы

- три уровня: **Старт**, **Стандарт**, **Премиум**;
- название, описания, фотография, цена, срок и график вознаграждений;
- сохранение условий в момент активации;
- реферальная ссылка каждого клиента;
- 10% пригласившему от покупки программы другом;
- дополнительно 2 USDT пригласившему при каждом вознаграждении друга по Premium.

### Лотереи

- публичный каталог и подробная страница;
- цена билета, начало продаж, дедлайн и дата результатов;
- общий лимит билетов и лимит на пользователя;
- денежные и неденежные призы, каждый с количеством призовых мест;
- покупка билетов с внутреннего USDT-баланса;
- уникальный код каждого билета;
- обязательное принятие версии правил при покупке;
- случайный выбор через `secrets.SystemRandom`;
- ручной выбор билета администратором;
- возможность отменить неподтверждённый выбор;
- отдельное подтверждение победителя администратором;
- денежный приз идемпотентно поступает на баланс;
- для неденежного приза пользователь получает поздравление и Telegram менеджера;
- email-уведомление и центр уведомлений в личном кабинете;
- публичный список только подтверждённых победителей с маскированным email;
- журнал аудита административных действий.

### Пополнения и выводы

- несколько адресов пополнения;
- текущая автоматическая проверка: USDT ERC-20 в Ethereum Mainnet через Infura;
- другие сети можно сохранить с отключённым мониторингом;
- уникальная сумма заявки и идемпотентное зачисление;
- вывод доступен по средам в часовом поясе `Asia/Almaty`;
- заявленный срок обработки вывода — от 1 часа до 3 дней.

### Интерфейс

- PNG-логотип и фотографии автомобилей;
- мобильное меню публичного сайта;
- выезжающее мобильное меню личного кабинета;
- мобильная навигация админ-панели;
- уведомления с непрочитанным счётчиком;
- актуальные лотереи на главной странице;
- публикации компании на главной странице.

## Первый запуск локально

Создайте env-файлы:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Для локального режима можно оставить:

```env
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

```env
# backend/.env
APP_ENV=development
DEBUG=true
JWT_SECRET=replace-with-long-random-secret
EMAIL_DELIVERY_ENABLED=false
DEPOSIT_MONITORING_ENABLED=false
```

Запуск:

```bash
docker compose build
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm api python scripts/create_admin.py
docker compose up -d
```

Адреса:

```text
Клиентский сайт: http://localhost:3000
Админ-панель:    http://localhost:3001
Backend:         http://localhost:8000
Swagger:         http://localhost:8000/docs
```

## Production-настройка

В корневом `.env` укажите публичный API, потому что Vite встраивает адрес во время сборки:

```env
POSTGRES_DB=subscriptions
POSTGRES_USER=automotive
POSTGRES_PASSWORD=replace-with-strong-password
DOCKER_DNS_PRIMARY=1.1.1.1
DOCKER_DNS_SECONDARY=8.8.8.8
API_BIND_HOST=127.0.0.1
CUSTOMER_FRONTEND_BIND_HOST=127.0.0.1
ADMIN_FRONTEND_BIND_HOST=127.0.0.1
VITE_API_BASE_URL=https://api.example.com/api/v1
VITE_APP_NAME=Automotive Club
VITE_ADMIN_APP_NAME=Панель управления
```

В `backend/.env` обязательно используйте тот же PostgreSQL login/password:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://automotive:replace-with-url-encoded-password@db:5432/subscriptions
JWT_SECRET=replace-with-long-random-secret
CORS_ORIGINS=https://example.com,https://www.example.com,https://admin.example.com
CUSTOMER_FRONTEND_URL=https://example.com

EMAIL_DELIVERY_ENABLED=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=mailer@example.com
SMTP_PASSWORD=replace-with-smtp-password
SMTP_FROM_EMAIL=mailer@example.com
SMTP_FROM_NAME=Automotive Club
SMTP_STARTTLS=true
SMTP_USE_SSL=false
```

Для Infura:

```env
DEPOSIT_MONITORING_ENABLED=true
INFURA_API_KEY=replace-with-infura-key
DEFAULT_DEPOSIT_ADDRESS=0x...
```

Подробности:

- [`COMPOSE_ENVIRONMENTS.md`](COMPOSE_ENVIRONMENTS.md)
- [`DEPLOY_DNS_LOTTERY_FIX.md`](DEPLOY_DNS_LOTTERY_FIX.md)
- [`EMAIL_SETUP.md`](EMAIL_SETUP.md)
- [`LOTTERY_SETUP.md`](LOTTERY_SETUP.md)
- [`INFURA_SETUP.md`](INFURA_SETUP.md)
- [`LEGAL_CONSENT_UPDATE.md`](LEGAL_CONSENT_UPDATE.md)

## Обновление работающего сервера

Используйте [`UPGRADE_EMAIL_LOTTERY.md`](UPGRADE_EMAIL_LOTTERY.md). Основные команды:

```bash
docker compose build \
  api deposit-worker reward-worker email-worker \
  customer-frontend admin-frontend

docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current
docker compose up -d --force-recreate
docker compose exec email-worker python -m app.workers.email_worker --check
docker compose ps -a
```

Ожидаемая миграция:

```text
0006_legal_consent_evidence (head)
```

Не выполняйте:

```bash
docker compose down -v
```

Эта команда удаляет PostgreSQL volume.

## Миграции

- `0001_initial` — исходная схема;
- `0002_add_late_deposit_flag` — поздние пополнения;
- `0003_business_logic` — уровни программ, рефералы, несколько кошельков;
- `0004_infura_erc20` — универсальные блокчейн-депозиты и Infura;
- `0005_email_lottery` — подтверждение email, восстановление пароля, согласия, очередь писем, уведомления и лотереи.
- `0006_legal_consent_evidence` — точная формулировка трёх чекбоксов, batch-id, email, URL документов и расширенный аудит электронного акцепта.

При переходе с `0004` существующие пользователи автоматически получают `email_verified_at=created_at`, поэтому их вход не блокируется. Новые аккаунты должны подтвердить email.

## Проверка после запуска

```bash
docker compose ps -a
docker compose logs api --tail=100
docker compose logs email-worker --tail=100
docker compose exec email-worker python -m app.workers.email_worker --check
docker compose logs reward-worker --tail=100
docker compose logs deposit-worker --tail=100
```

Проверьте API:

```bash
curl -i https://api.example.com/api/v1/plans
curl -i https://api.example.com/api/v1/lotteries
```

## Тестирование текущей версии

В рабочей версии проверены:

- 56 backend-тестов;
- регистрация, подтверждение email, повторная отправка и восстановление пароля;
- обязательные юридические согласия;
- изменение email с отзывом старой сессии;
- покупка билетов и списание баланса;
- случайный и ручной выбор победителя;
- подтверждение денежного и неденежного приза;
- уведомления и email-очередь;
- запрет преждевременного показа неподтверждённого победителя;
- AST-регрессия: у каждого `with_for_update` есть `of=Model`;
- Alembic upgrade на чистой БД;
- Alembic `0004 → 0005` с сохранением старого пользователя, баланса и операции;
- `alembic check` без расхождений;
- компиляция Python;
- синтаксический разбор 141 TypeScript/TSX-файла.

Frontend production-сборка выполняется Dockerfile-командой `npm ci && npm run build`. При изменении `VITE_API_BASE_URL` frontend необходимо пересобирать, а не только перезапускать.

## Юридическое замечание

Оплачиваемые лотереи и клиентские программы могут регулироваться по-разному в странах Центральной Азии и СНГ. Перед публичным запуском требуется проверить у профильного юриста правила розыгрыша, допустимость платных билетов, возраст участников, возвраты, налогообложение призов, требования к лицензиям и формулировки публичных документов.
