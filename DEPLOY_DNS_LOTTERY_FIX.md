# Развёртывание исправления email-worker и главной страницы

Дата: 22 августа 2026 года.

## 1. Один раз разделите общий и серверный Compose

Не редактируйте отслеживаемый Git-файл `docker-compose.yml` отдельно на сервере.
Перед первым переходом сохраните текущую серверную версию:

```bash
cp docker-compose.yml "$HOME/docker-compose.server.before-fix.yml"
git diff -- docker-compose.yml > "$HOME/docker-compose.server.before-fix.patch"
```

После `git pull` перенесите:

- отличающиеся значения — в корневой `.env`;
- отличающиеся секции/volumes/logging/networks — в `docker-compose.server.yml`.

Создание файлов без перезаписи уже существующих:

```bash
test -f .env || cp .env.example .env
test -f docker-compose.server.yml || \
  cp docker-compose.server.example.yml docker-compose.server.yml
```

`docker-compose.server.yml` и `.env` игнорируются Git. Подробная схема описана в
`COMPOSE_ENVIRONMENTS.md`.

## 2. Проверьте серверные значения

В корневом `.env`:

```env
DOCKER_RESTART_POLICY=unless-stopped
DOCKER_DNS_PRIMARY=1.1.1.1
DOCKER_DNS_SECONDARY=8.8.8.8

POSTGRES_BIND_HOST=127.0.0.1
API_BIND_HOST=127.0.0.1
CUSTOMER_FRONTEND_BIND_HOST=127.0.0.1
ADMIN_FRONTEND_BIND_HOST=127.0.0.1

VITE_API_BASE_URL=https://api.example.com/api/v1
```

В `backend/.env`:

```env
EMAIL_DELIVERY_ENABLED=true
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_STARTTLS=true
SMTP_USE_SSL=false
```

В `SMTP_HOST` нельзя добавлять `https://`, путь или `:587`.

Если хостинг блокирует публичные DNS-серверы, укажите в `DOCKER_DNS_PRIMARY` и
`DOCKER_DNS_SECONDARY` разрешённые DNS-адреса хостинга или вашей сети.

## 3. Проверьте объединённый Compose

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  config > /tmp/automotive-compose.rendered.yml
```

Команда должна завершиться без ошибки. В итоговой конфигурации проверьте сервис
`email-worker`, его `dns`, `env_file`, `command` и `healthcheck`.

## 4. Соберите и пересоздайте изменённые сервисы

Миграция БД для этого исправления не требуется.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  build api email-worker customer-frontend


docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  up -d --force-recreate api email-worker customer-frontend
```

## 5. Проверьте SMTP DNS

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  exec email-worker python -m app.workers.email_worker --check
```

Ожидаемый результат:

```text
SMTP DNS OK: smtp-relay.brevo.com:587 -> ...
```

Также проверьте состояние и журнал:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  ps -a


docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  logs email-worker --tail=200
```

Пока DNS не работает, worker оставляет новые письма в очереди и не расходует
их попытки. После восстановления DNS обработка продолжится автоматически.

## 6. Верните исчерпавшие попытки письма

Сначала исправьте DNS и убедитесь, что `--check` проходит. Затем:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  exec api python scripts/requeue_failed_emails.py
```

Команда по умолчанию возвращает только письма, достигшие
`EMAIL_WORKER_MAX_ATTEMPTS`. Для возврата всех писем со статусом `failed`:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  exec api python scripts/requeue_failed_emails.py --all-failed
```

## 7. Проверьте главную страницу

Откройте клиентский сайт после пересборки `customer-frontend`. На главной должен
появиться блок «Актуальные лотереи» и до трёх публичных лотерей.

Публичный API:

```bash
curl -i https://api.example.com/api/v1/lotteries?page=1\&page_size=3
```

Если API возвращает пустой список, опубликуйте лотерею в админ-панели. Черновики
на публичной главной намеренно не отображаются.
