# Обновление до подтверждения email и лотерей

Новые миграции: `0005_email_lottery` и `0006_legal_consent_evidence`.

Она:

- добавляет `pending_email` и `email_verified_at` пользователям;
- считает существующие аккаунты подтверждёнными, чтобы обновление не заблокировало текущих клиентов и администратора;
- создаёт одноразовые токены подтверждения email и восстановления пароля;
- создаёт журнал юридических согласий;
- сокращает форму до трёх чекбоксов, сохраняя пять версий документов;
- сохраняет batch-id, точную формулировку чекбокса, email и URL документов;
- создаёт транзакционную очередь писем;
- создаёт уведомления пользователя;
- создаёт таблицы лотерей, призов, покупок, билетов и победителей;
- расширяет типы операций кошелька для покупки билета, денежного приза и возврата;
- не изменяет существующие балансы, программы, подписки и операции.

## 1. Резервная копия

```bash
cd /opt/automotive/automotive_platform_workspace

docker compose exec db sh -lc 'pg_dump \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -Fc -f /tmp/before_email_lottery.dump'

docker compose cp db:/tmp/before_email_lottery.dump ./before_email_lottery.dump
```

## 2. Настройки

Создайте корневой env при его отсутствии:

```bash
cp .env.example .env
```

Проверьте в корневом `.env` production URL API:

```env
VITE_API_BASE_URL=https://api.automotiveclub.example/api/v1
```

Дополните `backend/.env` SMTP-параметрами из `EMAIL_SETUP.md` и проверьте:

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://POSTGRES_USER:URL_ENCODED_POSTGRES_PASSWORD@db:5432/POSTGRES_DB
CUSTOMER_FRONTEND_URL=https://automotiveclub.example
EMAIL_DELIVERY_ENABLED=true

REGISTRATION_CONSENT_FORM_VERSION=2026-08-10
TERMS_VERSION=2026-08-10
PRIVACY_POLICY_VERSION=2026-08-10
PERSONAL_DATA_PROCESSING_VERSION=2026-08-10
PROGRAM_RULES_VERSION=2026-08-10
AGE_CONFIRMATION_VERSION=2026-08-10
```

`DATABASE_URL` должен использовать те же `POSTGRES_USER`, `POSTGRES_PASSWORD` и `POSTGRES_DB`, что и корневой `.env`. Спецсимволы пароля необходимо URL-кодировать.

## 3. Сборка и миграция

```bash
docker compose build \
  api \
  deposit-worker \
  reward-worker \
  email-worker \
  customer-frontend \
  admin-frontend

docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm api alembic current
```

Ожидается:

```text
0006_legal_consent_evidence (head)
```

Запуск:

```bash
docker compose up -d --force-recreate
docker compose ps -a
```

## 4. Проверка

```bash
docker compose logs api --tail=100
docker compose logs email-worker --tail=100
docker compose logs reward-worker --tail=100

curl -I https://api.automotiveclub.example/docs
curl -i https://api.automotiveclub.example/api/v1/lotteries
```

Затем проверьте полный сценарий на отдельном тестовом email:

1. регистрация;
2. письмо подтверждения;
3. вход после подтверждения;
4. запрос восстановления пароля;
5. создание черновика лотереи;
6. добавление приза и публикация;
7. покупка билета тестовым пользователем;
8. выбор победителя после тестовой даты;
9. подтверждение и проверка баланса/уведомления.

## Важно

- Не запускайте `docker compose down -v`: это удалит volume PostgreSQL.
- После изменения `VITE_API_BASE_URL` обязательно пересобирайте frontend.
- После изменения Python-кода пересобирайте `api` и соответствующие worker-контейнеры.
- После изменения только `backend/.env` обычно достаточно `docker compose up -d --force-recreate api email-worker ...`.
