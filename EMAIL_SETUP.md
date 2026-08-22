# Подтверждение email и восстановление пароля

В проекте используется транзакционная очередь писем. HTTP-запрос не ждёт SMTP: backend создаёт одноразовый токен, сохраняет только его SHA-256-хеш, ставит письмо в `email_outbox`, а отдельный контейнер `email-worker` отправляет сообщение.

## Что работает

- подтверждение email после регистрации;
- запрет входа до подтверждения;
- повторная отправка письма с ограничением частоты;
- восстановление забытого пароля по одноразовой ссылке;
- отзыв всех старых refresh-сессий после смены пароля;
- подтверждение нового email при изменении профиля;
- отзыв старых сессий после подтверждения нового email;
- повторные попытки SMTP с увеличивающейся задержкой;
- lease сообщения очереди, защищающий от повторной отправки двумя worker-контейнерами.

## Production-настройки

Откройте `backend/.env` и задайте:

```env
APP_ENV=production
DEBUG=false
CUSTOMER_FRONTEND_URL=https://automotiveclub.example

EMAIL_DELIVERY_ENABLED=true
# Только hostname, без https:// и без :587.
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=mailer@example.com
SMTP_PASSWORD=replace-with-smtp-password
SMTP_FROM_EMAIL=mailer@example.com
SMTP_FROM_NAME=Automotive Club
SMTP_STARTTLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT_SECONDS=30

EMAIL_VERIFICATION_TTL_HOURS=24
PASSWORD_RESET_TTL_MINUTES=60
EMAIL_REQUEST_COOLDOWN_SECONDS=60
EMAIL_WORKER_INTERVAL_SECONDS=10
EMAIL_WORKER_BATCH_SIZE=20
EMAIL_WORKER_MAX_ATTEMPTS=8
```

Используйте один из двух вариантов защиты SMTP:

- порт `587`: `SMTP_STARTTLS=true`, `SMTP_USE_SSL=false`;
- порт `465`: `SMTP_STARTTLS=false`, `SMTP_USE_SSL=true`.

Одновременно включать оба режима нельзя.

`CUSTOMER_FRONTEND_URL` нужен для формирования ссылок:

```text
https://automotiveclub.example/verify-email?token=...
https://automotiveclub.example/reset-password?token=...
```

В production API намеренно не запускается, если `EMAIL_DELIVERY_ENABLED=false` или не заданы критические SMTP-параметры. Это не позволяет случайно открыть регистрацию без реально работающего подтверждения email.

## Запуск

```bash
docker compose build api email-worker
docker compose up -d --force-recreate api email-worker
docker compose ps -a
docker compose exec email-worker python -m app.workers.email_worker --check
docker compose logs email-worker --tail=100
```

Нормальная проверка:

```text
SMTP DNS OK: smtp.example.com:587 -> ...
```

После запуска `email-worker` также имеет Docker healthcheck. Пока SMTP hostname не
разрешается, worker не забирает новые письма из БД и не расходует их лимит попыток.
После восстановления DNS очередь продолжает обрабатываться автоматически.


## Ошибка `socket.gaierror: No address associated with hostname`

Эта ошибка возникает до SMTP-авторизации: контейнер не смог получить IP-адрес
для `SMTP_HOST`. Сначала проверьте конфигурацию и DNS внутри контейнера:

```bash
docker compose exec email-worker python -m app.workers.email_worker --check
docker compose config | sed -n '/email-worker:/,/^[^ ]/p'
```

Проверьте, что в `backend/.env` записано именно имя сервера:

```env
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
```

Нельзя указывать `https://smtp-relay.brevo.com`,
`smtp-relay.brevo.com:587` или URL с путём.

Корневой `docker-compose.yml` использует отдельные DNS-серверы для backend и
worker-контейнеров. Они задаются в корневом `.env` и не попадают в Git:

```env
DOCKER_DNS_PRIMARY=1.1.1.1
DOCKER_DNS_SECONDARY=8.8.8.8
```

После изменения пересоздайте контейнер:

```bash
docker compose up -d --build --force-recreate email-worker
docker compose exec email-worker python -m app.workers.email_worker --check
```

Если DNS уже работает, но соединение с портом `587` завершается timeout,
проверьте ограничения исходящего SMTP у хостинга. Для Brevo можно отдельно
попробовать порт `2525` с `SMTP_STARTTLS=true` и `SMTP_USE_SSL=false`.

### Возврат писем, исчерпавших попытки

Письма с `attempt_count`, достигшим `EMAIL_WORKER_MAX_ATTEMPTS`, автоматически
не забираются. После исправления SMTP/DNS верните только такие письма в очередь:

```bash
docker compose run --rm api python scripts/requeue_failed_emails.py
```

Чтобы немедленно вернуть все письма со статусом `failed`:

```bash
docker compose run --rm api \
  python scripts/requeue_failed_emails.py --all-failed
```

## Диагностика очереди

```bash
docker compose exec db sh -lc 'psql \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -c "
SELECT id, recipient_email, subject, status, attempt_count,
       available_at, sent_at, left(last_error, 200) AS last_error
FROM email_outbox
ORDER BY created_at DESC
LIMIT 30;
"'
```

Статусы:

- `pending` — ожидает отправки;
- `sending` — сообщение забрано worker и имеет временный lease;
- `sent` — успешно отправлено;
- `failed` — SMTP вернул ошибку; worker повторит попытку после задержки.

После успешной отправки текст и HTML письма очищаются, чтобы одноразовая ссылка не оставалась в базе в открытом виде.

## Development

При:

```env
APP_ENV=development
EMAIL_DELIVERY_ENABLED=false
```

SMTP не требуется. Тестовый токен возвращается frontend и позволяет пройти сценарий локально. В production тестовые токены никогда не возвращаются.

## Безопасность

- не публикуйте `SMTP_PASSWORD`, `JWT_SECRET` и `.env`;
- используйте отдельный SMTP-пароль или API-пароль провайдера;
- включите SPF, DKIM и DMARC для домена отправителя;
- отправляйте письма с адреса вашего домена;
- после смены SMTP-пароля пересоздайте `api` и `email-worker`.
