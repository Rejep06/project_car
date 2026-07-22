# Карта фактического FastAPI API

Документ составлен по реальным FastAPI routers, Pydantic-схемам и сгенерированному OpenAPI после минимальных изменений для browser frontend. Базовый URL в development:

```text
http://localhost:8000/api/v1
```

Сгенерированный OpenAPI после frontend-правок содержит **55 paths и 63 HTTP-операции**. Все пути в `src/api/` обоих приложений были автоматически сопоставлены с этой схемой.

## Общие правила

- Денежные значения передаются строками с шестью знаками после запятой: `"100.347000"`.
- Идентификаторы — UUID-строки.
- Даты — ISO 8601 UTC.
- Пагинация: `page`, `page_size`; ответ: `{items, page, page_size, total}`.
- Защищённые маршруты принимают `Authorization: Bearer <access_token>`.
- Покупка подписки и корректировка баланса используют `Idempotency-Key`.
- Ошибка приложения:

```json
{
  "error": {
    "code": "insufficient_balance",
    "message": "Недостаточно средств",
    "details": {}
  }
}
```

## Авторизация и системные настройки

| Интерфейс | Метод | Endpoint | Назначение | Роль | Основные данные |
|---|---:|---|---|---|---|
| Оба приложения | GET | `/system/config` | Безопасные публичные лимиты для форм | public | asset, network, минимальные суммы, комиссия, сроки 30/24, лимиты файлов |
| Регистрация клиента | POST | `/auth/register` | Создать пользователя и кошелёк | public | email, password → UserRead |
| Вход | POST | `/auth/login` | Получить пару JWT | public | email, password → access_token, refresh_token, expires_in |
| Восстановление сессии | POST | `/auth/refresh` | Ротация refresh token | public | refresh_token → новая пара токенов |
| Выход | POST | `/auth/logout` | Отозвать refresh session | public | refresh_token |
| Профиль | GET | `/users/me` | Текущий пользователь и роль | user/admin | UserRead |
| Профиль клиента | PATCH | `/users/me` | Изменить email или пароль | user/admin | UserUpdate → UserRead |

## Клиентский сайт

| Страница | Метод | Endpoint | Назначение | Роль | Основные данные |
|---|---:|---|---|---|---|
| `/`, `/plans` | GET | `/plans` | Активные программы | public | PlanRead: title, slug, price, срок, reward amount/frequency/duration |
| `/plans/:slug` | GET | `/plans/{slug}` | Условия выбранной программы | public | PlanRead |
| `/plans/:slug` | POST | `/subscriptions/{plan_id}/purchase` | Купить подписку | user | Header `Idempotency-Key`; ответ UserSubscriptionRead |
| `/account/subscriptions` | GET | `/subscriptions` | Купленные программы | user | Pagination<UserSubscriptionRead> |
| `/account/subscriptions/:id` | GET | `/subscriptions/{subscription_id}` | Снимок условий и точный RewardPayout-график | user | UserSubscriptionRead с `reward_payouts` |
| `/account`, `/account/wallet` | GET | `/wallet` | Доступный и locked balance | user | WalletRead |
| `/account/transactions`, `/account/rewards` | GET | `/wallet/transactions` | Журнал операций; reward UI фильтрует `reward_credit` | user | Pagination<WalletTransactionRead> |
| `/account/deposits` | POST | `/wallet/deposits` | Создать заявку с точной суммой | user | `{amount: string}` → DepositInvoiceRead |
| `/account/deposits` | GET | `/wallet/deposits` | Список заявок | user | Pagination<DepositInvoiceRead> |
| `/account/deposits/:id` | GET | `/wallet/deposits/{invoice_id}` | Сроки, сумма, адрес, late-credit flag | user | DepositInvoiceRead |
| `/account/withdrawals` | POST | `/wallet/withdrawals` | Заблокировать сумму и создать ручной вывод | user | destination_address, amount → WithdrawalRead |
| `/account/withdrawals` | GET | `/wallet/withdrawals` | История выводов | user | Pagination<WithdrawalRead> |
| `/account/withdrawals` | GET | `/wallet/withdrawals/{withdrawal_id}` | Детали вывода | user | WithdrawalRead |
| `/account/withdrawals` | POST | `/wallet/withdrawals/{withdrawal_id}/cancel` | Отменить до admin approval | user | WithdrawalRead |
| `/news` | GET | `/posts` | Опубликованные новости | public | Pagination<PostRead> |
| `/news/:slug` | GET | `/posts/{slug}` | Опубликованная новость | public | PostRead |
| `/account/support` | POST | `/support/tickets` | Создать обращение | user | category, subject, message, txid?, related invoice? |
| `/account/support` | GET | `/support/tickets` | Только обращения текущего пользователя | user | Pagination<TicketRead> |
| `/account/support/:id` | GET | `/support/tickets/{ticket_id}` | Сообщения и статус своего обращения | user | TicketRead |
| `/account/support/:id` | POST | `/support/tickets/{ticket_id}/messages` | Добавить сообщение/TxID | user | MessageCreate → MessageRead |
| `/account/support` | POST | `/support/messages/{message_id}/attachments` | До 3 PNG/JPG/JPEG/WEBP/PDF, 5 MB каждый | user | multipart files → AttachmentRead[] |
| `/account/support/:id` | GET | `/support/attachments/{attachment_id}` | Защищённое скачивание | owner/admin | Binary response |

## Административная панель

| Страница | Метод | Endpoint | Назначение | Роль | Основные данные |
|---|---:|---|---|---|---|
| `/` | GET | несколько пагинированных list endpoints | Dashboard использует только `total` и первые записи | admin | Без загрузки всех объектов |
| `/plans` | GET | `/admin/plans` | Все программы, включая неактивные | admin | Pagination<PlanRead> |
| `/plans/new` | POST | `/admin/plans` | Создать программу | admin | PlanCreate → PlanRead |
| `/plans/:id` | GET | `/admin/plans/{plan_id}` | Получить программу | admin | PlanRead |
| `/plans/:id` | PATCH | `/admin/plans/{plan_id}` | Изменить программу | admin | PlanUpdate → PlanRead |
| `/plans/:id` | POST | `/admin/plans/{plan_id}/activate` | Активировать | admin | PlanRead |
| `/plans/:id` | POST | `/admin/plans/{plan_id}/deactivate` | Деактивировать | admin | PlanRead |
| `/users` | GET | `/admin/users` | Пользователи с available/locked balance | admin | Pagination<AdminUserRead> |
| `/users/:id` | GET | `/admin/users/{user_id}` | Профиль и кошелёк пользователя | admin | AdminUserRead |
| `/users/:id` | POST | `/admin/users/{user_id}/freeze` | Заморозить | admin | AdminUserRead |
| `/users/:id` | POST | `/admin/users/{user_id}/unfreeze` | Разморозить | admin | AdminUserRead |
| `/users/:id` | POST | `/admin/users/{user_id}/balance-adjustment` | Корректировка через WalletService | admin | amount, description + Idempotency-Key |
| `/deposits` | GET | `/admin/deposits/unmatched` | Нераспознанные депозиты | admin | Pagination<UnmatchedDepositRead>: внешний Binance ID, TxID, coin, сумма, сеть, время, причина, статус, возможные связи, признак использованного TxID |
| `/deposits/:id` | GET | `/admin/deposits/unmatched/{unmatched_id}` | Детали | admin | UnmatchedDepositRead с `binance_record_id`, `binance_deposit_id`, `binance_status`, `deposit_time`, `credited_at`, `txid_already_used` |
| `/deposits/:id` | POST | `/admin/deposits/unmatched/{unmatched_id}/assign` | Проверить и зачислить фактическую сумму | admin | user_id, invoice_id?; idempotency внутри backend |
| `/deposits/:id` | POST | `/admin/deposits/unmatched/{unmatched_id}/ignore` | Игнорировать запись | admin | UnmatchedDepositRead |
| `/withdrawals` | GET | `/admin/withdrawals` | Все ручные выводы | admin | Pagination<AdminWithdrawalRead> |
| `/withdrawals/:id` | GET | `/admin/withdrawals/{withdrawal_id}` | Детали вывода | admin | AdminWithdrawalRead |
| `/withdrawals/:id` | POST | `/admin/withdrawals/{withdrawal_id}/approve` | Подтвердить проверку | admin | AdminWithdrawalRead |
| `/withdrawals/:id` | POST | `/admin/withdrawals/{withdrawal_id}/reject` | Отклонить и вернуть hold | admin | `{comment}` |
| `/withdrawals/:id` | POST | `/admin/withdrawals/{withdrawal_id}/mark-sent` | Сохранить TxID после ручного Binance-перевода | admin | txid, actual_fee, comment? |
| `/withdrawals/:id` | POST | `/admin/withdrawals/{withdrawal_id}/complete` | Завершить и уменьшить locked balance | admin | comment? |
| `/support` | GET | `/admin/support/tickets` | Все обращения | admin | Pagination<AdminTicketRead> |
| `/support/:id` | GET | `/admin/support/tickets/{ticket_id}` | Пользователь, заявка, Binance data, сообщения, конфликт TxID | admin | AdminTicketRead |
| `/support/:id` | POST | `/admin/support/tickets/{ticket_id}/messages` | Ответить | admin | MessageCreate → MessageRead |
| `/support/:id` | POST | `/admin/support/tickets/{ticket_id}/status` | Изменить статус | admin | TicketStatusUpdate |
| `/support/:id` | POST | `/admin/support/tickets/{ticket_id}/resolve-deposit` | Проверить и вручную зачислить реальный депозит | admin | invoice_id? → AdminTicketRead |
| `/posts` | GET | `/admin/posts` | Все новости | admin | Pagination<PostRead> |
| `/posts/new` | POST | `/admin/posts` | Создать черновик | admin | PostCreate |
| `/posts/:id` | GET | `/admin/posts/{post_id}` | Получить черновик/новость по UUID | admin | PostRead |
| `/posts/:id` | PATCH | `/admin/posts/{post_id}` | Изменить | admin | PostUpdate |
| `/posts/:id` | POST | `/admin/posts/{post_id}/publish` | Опубликовать | admin | PostRead |
| `/posts/:id` | POST | `/admin/posts/{post_id}/archive` | Архивировать | admin | PostRead |
| `/audit` | GET | `/admin/audit-logs` | Неизменяемый audit log | admin | Pagination<AuditLogRead> |

## Сроки пополнения в фактическом API

`DepositInvoiceRead` возвращает `expires_at`, `amount_reserved_until`, `credited_after_expiration` и статус.

- `deposit_time <= expires_at`: обычное автоматическое зачисление.
- `expires_at < deposit_time <= amount_reserved_until`: позднее автоматическое зачисление, `credited_after_expiration=true`.
- `deposit_time > amount_reserved_until`: автоматического зачисления нет, требуется поддержка.
- Неправильная сумма автоматически не зачисляется.

## API, которого нет

Frontend не подменяет следующие отсутствующие возможности фиктивными маршрутами:

1. Отдельный агрегированный admin dashboard endpoint.
2. Серверный поиск/фильтры по TxID, причине и статусу для admin lists. Фильтры интерфейса действуют только на текущую страницу.
3. Admin subresource endpoints вида `/admin/users/{id}/subscriptions|transactions|deposits|withdrawals|tickets`.
4. Отдельный список всех будущих reward payouts. Точный график доступен внутри `GET /subscriptions/{id}`; фактические начисления — в wallet transactions.
5. Отдельное поле `reported_amount_atomic` в TicketCreate. Клиент сохраняет фактическую сумму в первом сообщении, не выдавая её за структурированное поле.
6. KYC endpoints.
7. Endpoint логотипа/контента компании; тексты сайта редактируются в `src/config/content.ts`.
8. Binance withdrawal/trading endpoints — намеренно отсутствуют.

## Минимальные изменения backend для frontend

- Добавлен явный CORS для `http://localhost:3000` и `http://localhost:3001`; `*` запрещён в production.
- Добавлен `GET /system/config`, который не возвращает JWT/Binance/DB-секреты.
- Добавлен `GET /admin/posts/{post_id}`, потому что форма редактирования должна открывать существующий черновик по UUID.
- Ответ `UnmatchedDepositRead` дополнен реальным Binance deposit ID, монетой, временем, Binance-статусом и признаком уже использованного TxID; это вычисляемые поля без изменения БД.
- Миграции БД для этих изменений не требуются.
