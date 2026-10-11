# Карта FastAPI API

Базовый URL:

```text
http://localhost:8000/api/v1
```

Актуальный OpenAPI содержит **88 paths и 101 HTTP-операция**. Полная машинная схема находится в `BACKEND_OPENAPI.json`.

## Авторизация и профиль

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/system/config` | Публичные лимиты, процент комиссии `withdrawal_fee_percent`, окно вывода и условия реферальной программы |
| POST | `/auth/register` | Регистрация с обязательными юридическими согласиями и отправкой подтверждения email |
| POST | `/auth/email-verification/confirm` | Подтвердить email по одноразовому токену |
| POST | `/auth/email-verification/resend` | Повторно запросить письмо подтверждения |
| POST | `/auth/password-reset/request` | Запросить ссылку восстановления пароля |
| POST | `/auth/password-reset/confirm` | Установить новый пароль и отозвать старые сессии |
| POST | `/auth/login` | Получение access/refresh token после подтверждения email |
| POST | `/auth/refresh` | Восстановление сессии и ротация refresh token |
| POST | `/auth/logout` | Завершение серверной сессии |
| GET | `/users/me` | Текущий пользователь |
| PATCH | `/users/me` | Запрос подтверждения нового email |

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

## Лотереи и уведомления

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/lotteries` | Публичный каталог опубликованных лотерей |
| GET | `/lotteries/{lottery_id}` | Условия, призы и подтверждённые победители |
| POST | `/lotteries/{lottery_id}/tickets` | Купить билеты с баланса; требуется `Idempotency-Key` |
| GET | `/lotteries/me/tickets` | Все билеты и подтверждённые призы пользователя |
| GET | `/lotteries/{lottery_id}/my-tickets` | Билеты пользователя в конкретной лотерее |
| GET | `/notifications` | Уведомления текущего пользователя |
| GET | `/notifications/unread-count` | Счётчик непрочитанных уведомлений |
| POST | `/notifications/{notification_id}/read` | Отметить уведомление прочитанным |
| POST | `/notifications/read-all` | Прочитать все уведомления |

## Публикации и поддержка

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/posts` | Опубликованные материалы |
| GET | `/posts/{slug}` | Одна публикация |
| POST | `/support/tickets` | Создать обращение |
| GET | `/support/tickets` | Обращения пользователя с `unread_count` |
| GET | `/support/unread-count` | Число непрочитанных входящих сообщений поддержки |
| POST | `/support/tickets/{ticket_id}/read` | Прочитать перечисленные входящие `message_ids`; возвращает общий `unread_count` |
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
| POST | `/admin/deposit-wallets` | Добавить адрес любой сети; автопроверка сейчас только Ethereum/USDT ERC-20/Infura |
| GET | `/admin/deposit-wallets/{wallet_id}` | Получить адрес |
| PATCH | `/admin/deposit-wallets/{wallet_id}` | Изменить, включить или отключить адрес |
| GET | `/admin/deposits/unmatched` | Нераспознанные пополнения |
| GET | `/admin/deposits/unmatched/{unmatched_id}` | Детали пополнения |
| POST | `/admin/deposits/unmatched/{unmatched_id}/assign` | Связать и зачислить |
| POST | `/admin/deposits/unmatched/{unmatched_id}/ignore` | Игнорировать запись |

## Администратор: лотереи

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/admin/lotteries` | Все лотереи |
| POST | `/admin/lotteries` | Создать черновик |
| GET | `/admin/lotteries/{lottery_id}` | Лотерея, призы, билеты и победители |
| PATCH | `/admin/lotteries/{lottery_id}` | Изменить лотерею |
| POST | `/admin/lotteries/{lottery_id}/publish` | Опубликовать продажи билетов |
| POST | `/admin/lotteries/{lottery_id}/prizes` | Добавить приз |
| PATCH | `/admin/lotteries/{lottery_id}/prizes/{prize_id}` | Изменить приз до первой продажи |
| DELETE | `/admin/lotteries/{lottery_id}/prizes/{prize_id}` | Удалить приз до первой продажи |
| GET | `/admin/lotteries/{lottery_id}/tickets` | Билеты; поддерживается поиск по коду и email |
| POST | `/admin/lotteries/{lottery_id}/draw-random` | Случайно выбрать победителей после `draw_at` |
| POST | `/admin/lotteries/{lottery_id}/winners/manual` | Выбрать конкретный билет вручную |
| DELETE | `/admin/lotteries/winners/{winner_id}` | Отменить неподтверждённый выбор |
| POST | `/admin/lotteries/winners/{winner_id}/confirm` | Подтвердить приз и выдать его |
| POST | `/admin/lotteries/{lottery_id}/winners/confirm-all` | Подтвердить всех ожидающих победителей |

## Администратор: выводы, публикации, поддержка

| Метод | Endpoint | Назначение |
|---|---|---|
| GET | `/admin/withdrawals` | Все заявки на вывод |
| GET | `/admin/withdrawals/{withdrawal_id}` | Детали заявки |
| PATCH | `/admin/withdrawals/{withdrawal_id}/amounts` | Исправить `amount`, `fee` и баланс с причиной `comment`, `expected_updated_at` и `Idempotency-Key` |
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
| GET | `/admin/support/unread-count` | Число непрочитанных входящих сообщений пользователей |
| POST | `/admin/support/tickets/{ticket_id}/read` | Прочитать перечисленные входящие `message_ids` |
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
