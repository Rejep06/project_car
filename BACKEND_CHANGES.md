# Изменения backend

## Миграция `0003_business_logic`

- уровни программ starter/standard/premium;
- реферальные коды и связи;
- несколько кошельков пополнения;
- снимок условий активированной программы;
- отказ от program slug/category.

## Миграция `0004_infura_erc20`

- универсальные блокчейн-депозиты;
- Ethereum Mainnet + USDT ERC-20 + Infura;
- `network + txid + log_index` как идентификатор события;
- block number/hash, sender, provider, contract и confirmations;
- `blockchain_sync_states`;
- безопасное отключение старых неподдерживаемых адресов.

## Миграция `0005_email_lottery`

### Email и аккаунт

- `users.pending_email`;
- `users.email_verified_at`;
- `email_verification_tokens`;
- `password_reset_tokens`;
- `email_outbox`;
- `email-worker`;
- подтверждение регистрации;
- подтверждение нового email;
- восстановление пароля;
- отзыв старых refresh-сессий.

### Юридические согласия

- `legal_consents`;
- тип и версия документа;
- время, IP и User-Agent;
- обязательные условия, privacy, персональные данные, правила и 18+.

### Лотереи

- `lotteries`;
- `lottery_prizes`;
- `lottery_ticket_purchases`;
- `lottery_tickets`;
- `lottery_winners`;
- `user_notifications`;
- покупка билета с USDT-баланса;
- случайный и ручной выбор;
- подтверждение администратора;
- денежный приз на баланс;
- неденежный приз с контактом менеджера;
- публичные подтверждённые победители;
- audit log.

### Операции кошелька

Добавлены:

```text
lottery_ticket_purchase
lottery_prize_credit
lottery_ticket_refund
```

## Исправление PostgreSQL locking

Во всех runtime-запросах:

```python
.with_for_update()
```

заменено на блокировку конкретной таблицы:

```python
.with_for_update(of=Model)
```

Для пакетной обработки:

```python
.with_for_update(of=Model, skip_locked=True)
```

Это устраняет ошибку:

```text
FOR UPDATE cannot be applied to the nullable side of an outer join
```

Исправлены auth sessions, wallets, posts, rewards, plans, deposits, withdrawals, support, notifications, email outbox и lottery-запросы.

## Миграция `0006_legal_consent_evidence`

Форма регистрации сокращена до трёх видимых обязательных подтверждений, при этом backend продолжает хранить пять отдельных версий документов. Для новых записей `legal_consents` добавлены batch-id, версия формы, группа согласия, email-снимок, URL документа и точная формулировка чекбокса.
