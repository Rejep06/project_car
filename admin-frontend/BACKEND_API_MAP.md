# Карта FastAPI API

Базовый URL:

```text
http://localhost:8000/api/v1
```

Актуальный OpenAPI содержит **59 paths и 69 HTTP-операций**. Полная машинная схема находится в `BACKEND_OPENAPI.json`.

## Авторизация и профиль

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/system/config` | Публичные лимиты, окно вывода и условия реферальной программы |
| POST | `/auth/register` | Регистрация, включая необязательный реферальный код |
| POST | `/auth/login` | Получение access/refresh token |
| POST | `/auth/refresh` | Восстановление сессии и ротация refresh token |
| POST | `/auth/logout` | Завершение серверной сессии |
| GET | `/users/me` | Текущий пользователь |
| PATCH | `/users/me` | Изменение email или пароля |

## Клиентские программы

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/plans` | Активные программы уровней starter/standard/premium |
| GET | `/plans/{plan_id}` | Получение программы по UUID |
| POST | `/subscriptions/{plan_id}/purchase` | Активация программы; требуется `Idempotency-Key` |
| GET | `/subscriptions` | Программы текущего пользователя |
| GET | `/subscriptions/{subscription_id}` | Условия и график конкретной активированной программы |

## Кошелёк, пополнения и выводы

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/wallet` | Доступный и заблокированный баланс |
| GET | `/wallet/transactions` | История операций, включая реферальные бонусы |
| GET | `/wallet/deposit-addresses` | Активные адреса пополнения |
| POST | `/wallet/deposits` | Создание заявки с выбранным `deposit_wallet_id` |
| GET | `/wallet/deposits` | Список заявок на пополнение |
| GET | `/wallet/deposits/{invoice_id}` | Реквизиты и статус заявки |
| POST | `/wallet/withdrawals` | Создание заявки только в разрешённую среду |
| GET | `/wallet/withdrawals` | История выводов |
| GET | `/wallet/withdrawals/{withdrawal_id}` | Детали заявки |
| POST | `/wallet/withdrawals/{withdrawal_id}/cancel` | Отмена заявки до обработки |

## Реферальная программа

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/referrals/me` | Личная ссылка, код, статистика и приглашённые пользователи |

## Публикации и поддержка

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/posts` | Опубликованные материалы |
| GET | `/posts/{slug}` | Одна публикация |
| POST | `/support/tickets` | Создать обращение |
| GET | `/support/tickets` | Обращения пользователя |
| GET | `/support/tickets/{ticket_id}` | Детали обращения |
| POST | `/support/tickets/{ticket_id}/messages` | Добавить сообщение |
| POST | `/support/messages/{message_id}/attachments` | Добавить вложения |
| GET | `/support/attachments/{attachment_id}` | Скачать доступное вложение |

## Администратор: программы и пользователи

| Метод | Endpoint | Назначение |
|---|---|---|
| POST | `/admin/plans` | Создать программу |
| GET | `/admin/plans` | Все программы |
| GET | `/admin/plans/{plan_id}` | Одна программа |
| PATCH | `/admin/plans/{plan_id}` | Изменить программу |
| POST | `/admin/plans/{plan_id}/activate` | Активировать программу |
| POST | `/admin/plans/{plan_id}/deactivate` | Деактивировать программу |
| GET | `/admin/users` | Пользователи и балансы |
| GET | `/admin/users/{user_id}` | Пользователь и реферальные данные |
| POST | `/admin/users/{user_id}/freeze` | Заморозить аккаунт |
| POST | `/admin/users/{user_id}/unfreeze` | Разморозить аккаунт |
| POST | `/admin/users/{user_id}/balance-adjustment` | Корректировка баланса |

## Администратор: адреса и пополнения

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/admin/deposit-wallets` | Все адреса пополнения |
| POST | `/admin/deposit-wallets` | Добавить адрес |
| GET | `/admin/deposit-wallets/{wallet_id}` | Получить адрес |
| PATCH | `/admin/deposit-wallets/{wallet_id}` | Изменить, включить или отключить адрес |
| GET | `/admin/deposits/unmatched` | Нераспознанные пополнения |
| GET | `/admin/deposits/unmatched/{unmatched_id}` | Детали пополнения |
| POST | `/admin/deposits/unmatched/{unmatched_id}/assign` | Связать и зачислить |
| POST | `/admin/deposits/unmatched/{unmatched_id}/ignore` | Игнорировать запись |

## Администратор: выводы, публикации, поддержка

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/admin/withdrawals` | Все заявки на вывод |
| GET | `/admin/withdrawals/{withdrawal_id}` | Детали заявки |
| POST | `/admin/withdrawals/{withdrawal_id}/approve` | Подтвердить заявку |
| POST | `/admin/withdrawals/{withdrawal_id}/reject` | Отклонить и вернуть средства |
| POST | `/admin/withdrawals/{withdrawal_id}/mark-sent` | Сохранить TxID и фактическую комиссию |
| POST | `/admin/withdrawals/{withdrawal_id}/complete` | Завершить заявку |
| POST | `/admin/posts` | Создать черновик; slug может быть сформирован автоматически |
| GET | `/admin/posts` | Все публикации |
| GET | `/admin/posts/{post_id}` | Одна публикация по UUID |
| PATCH | `/admin/posts/{post_id}` | Изменить публикацию |
| POST | `/admin/posts/{post_id}/publish` | Опубликовать |
| POST | `/admin/posts/{post_id}/archive` | Архивировать |
| GET | `/admin/support/tickets` | Все обращения |
| GET | `/admin/support/tickets/{ticket_id}` | Детали обращения |
| POST | `/admin/support/tickets/{ticket_id}/messages` | Ответить пользователю |
| POST | `/admin/support/tickets/{ticket_id}/status` | Изменить статус |
| POST | `/admin/support/tickets/{ticket_id}/resolve-deposit` | Разрешить проблему пополнения |
| GET | `/admin/audit-logs` | Журнал административных действий |

## Денежные и временные правила

- Все суммы передаются строками с шестью знаками после точки.
- Изменения баланса создают отдельные операции и защищены ключами идемпотентности.
- Окно вывода рассчитывается сервером по часовому поясу `Asia/Almaty`.
- Реферальный бонус активации равен 10% от цены программы.
- Премиальный реферальный бонус равен 2 USDT за каждое фактическое начисление приглашённого пользователя.
