# Изменения: email, юридические согласия и лотереи

## Авторизация

Добавлены endpoints:

```text
POST /api/v1/auth/email-verification/confirm
POST /api/v1/auth/email-verification/resend
POST /api/v1/auth/password-reset/request
POST /api/v1/auth/password-reset/confirm
```

Регистрация больше не выдаёт JWT. Она создаёт аккаунт, кошелёк, записи согласий и письмо подтверждения. Вход до подтверждения возвращает `email_not_verified`.

## Юридические согласия

На форме регистрации показываются три обязательных чекбокса:

1. Пользовательское соглашение + Правила программ и лотерей.
2. Политика конфиденциальности + отдельное согласие на обработку персональных данных.
3. Возраст 18+, дееспособность, действия от своего имени и достоверность данных.

Backend по-прежнему сохраняет пять отдельных документов с собственными версиями. Миграция `0006_legal_consent_evidence` дополнительно фиксирует общий batch-id, версию формы, группу согласия, email-снимок, URL документа и точную формулировку видимого чекбокса, а также время, IP и User-Agent.

## Лотереи

Добавлены публичные и административные endpoints для каталога, покупки билетов, призов, случайного и ручного выбора, подтверждения победителей и пользовательских уведомлений.

## База

Новые основные таблицы:

```text
email_verification_tokens
password_reset_tokens
legal_consents
email_outbox
user_notifications
lotteries
lottery_prizes
lottery_ticket_purchases
lottery_tickets
lottery_winners
```

## Конкурентные блокировки

Все runtime-вызовы SQLAlchemy `with_for_update` теперь имеют явный `of=Model`. Это устраняет ошибку PostgreSQL:

```text
FOR UPDATE cannot be applied to the nullable side of an outer join
```

Регрессионный AST-тест не допускает возврат неявной блокировки.

## Исправление DNS email-worker и главная страница — 22 августа 2026

- `SMTP_HOST` нормализуется и проверяется: URL, путь и `host:port` отклоняются при запуске.
- Добавлена отдельная команда `python -m app.workers.email_worker --check` и Docker healthcheck.
- Пока SMTP hostname не разрешается, worker не забирает новые письма и не расходует лимит попыток.
- Если DNS пропадает между проверкой и отправкой, письмо возвращается в очередь без увеличения `attempt_count`.
- Добавлен скрипт `backend/scripts/requeue_failed_emails.py` для возврата исчерпавших попытки писем.
- В Compose добавлены настраиваемые DNS-серверы контейнеров.
- На главной странице клиентского сайта появился блок актуальных лотерей; карточка вынесена в общий компонент `LotteryCard`.
- Машинно-зависимые значения Compose перенесены в игнорируемый `.env`; структурные серверные отличия можно хранить в игнорируемом `docker-compose.server.yml`.
