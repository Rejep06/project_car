# Automotive Platform Backend

FastAPI backend Automotive Club: аккаунты, подтверждение email, внутренний USDT-баланс, клиентские программы, вознаграждения, Ethereum/Infura-пополнения, выводы, рефералы, публикации, поддержка, уведомления и лотереи.

## Технологии

- FastAPI;
- SQLAlchemy 2 async;
- PostgreSQL;
- Alembic;
- JWT access/refresh sessions;
- SMTP outbox worker;
- Ethereum JSON-RPC через Infura;
- фоновые workers;
- pytest.

## Авторизация и email

Регистрация требует пять юридических согласий и создаёт неподтверждённый аккаунт. JWT выдаётся только после подтверждения email.

```text
POST /api/v1/auth/register
POST /api/v1/auth/email-verification/confirm
POST /api/v1/auth/email-verification/resend
POST /api/v1/auth/password-reset/request
POST /api/v1/auth/password-reset/confirm
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

Одноразовые токены генерируются криптографически стойко. В БД сохраняется только SHA-256-хеш. После смены пароля или подтверждения нового email все старые refresh-сессии отзываются.

Письма сначала фиксируются в `email_outbox`, затем отправляются `email-worker`. Подробности: `../EMAIL_SETUP.md`.

## Юридические согласия

`legal_consents` сохраняет:

- пользователя;
- тип документа;
- версию;
- время;
- IP;
- User-Agent.

Типы документов:

```text
terms_of_use
privacy_policy
personal_data_processing
program_rules
age_confirmation
```

## Лотереи

Основные сущности:

```text
lotteries
lottery_prizes
lottery_ticket_purchases
lottery_tickets
lottery_winners
user_notifications
```

Билет оплачивается через `WalletService` операцией `lottery_ticket_purchase`. Денежный приз выдаётся операцией `lottery_prize_credit` с уникальным idempotency key победителя.

Выбор победителей:

- случайный — `secrets.SystemRandom`;
- ручной — администратор выбирает конкретный билет;
- результат становится клиентским только после подтверждения администратора.

Публичные endpoints:

```text
GET  /api/v1/lotteries
GET  /api/v1/lotteries/{id}
GET  /api/v1/lotteries/me/tickets
GET  /api/v1/lotteries/{id}/my-tickets
POST /api/v1/lotteries/{id}/tickets
```

Административные endpoints находятся под `/api/v1/admin/lotteries`.

## Конкурентность

Все вызовы SQLAlchemy `with_for_update` содержат явный параметр `of=Model`. Это важно при relationships с eager `LEFT OUTER JOIN`: PostgreSQL не разрешает блокировать nullable-сторону outer join.

Пакетные workers используют:

```python
.with_for_update(of=Model, skip_locked=True)
```

Тест `test_locking_regressions.py` анализирует AST всех runtime-файлов и не допускает неявный `FOR UPDATE`.

## Клиентские программы и рефералы

У программы есть уровень `starter`, `standard` или `premium`, название, описания, фото, цена, срок и график вознаграждений. Финансовые условия копируются в пользовательскую активацию.

Реферальная логика:

- 10% от каждой активации приглашённого;
- 2 USDT за каждое вознаграждение приглашённого по Premium;
- все начисления идемпотентны.

## Ethereum/Infura

Автоматический мониторинг поддерживает:

```text
Ethereum Mainnet
USDT ERC-20
Infura JSON-RPC
Contract: 0xdac17f958d2ee523a2206206994597c13d831ec7
Decimals: 6
```

`deposit-worker` читает подтверждённые события `Transfer`, сохраняет их в `blockchain_deposits` и сопоставляет с заявками по адресу и точной сумме. Курсор хранится в `blockchain_sync_states`.

## Запуск

```bash
cp .env.example .env
docker compose up -d db
docker compose build api deposit-worker reward-worker email-worker
docker compose run --rm api alembic upgrade head
docker compose run --rm api python scripts/create_admin.py
docker compose up -d
```

При запуске из общего workspace используйте корневой `docker-compose.yml`.

## Миграции

```bash
alembic upgrade head
alembic current
alembic history
alembic check
```

Последняя миграция:

```text
0006_legal_consent_evidence
```

Миграции `0005` и `0006` добавляют email verification, password reset, consent audit, outbox, notifications, lottery-модель и расширенные доказательства электронного акцепта. Существующие пользователи автоматически остаются подтверждёнными.

## Тесты

```bash
pytest -q
```

Текущий набор: 56 тестов. Покрыты авторизация, email, согласия, программы, rewards, рефералы, Ethereum-пополнения, выводы, поддержка, публикации, лотереи, уведомления, idempotency и PostgreSQL locking regressions.

## API

После запуска:

```text
Swagger: http://localhost:8000/docs
ReDoc:   http://localhost:8000/redoc
Health:  http://localhost:8000/health
```

Статическая схема OpenAPI находится в `../BACKEND_OPENAPI.json`.
