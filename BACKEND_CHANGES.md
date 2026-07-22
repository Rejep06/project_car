# Минимальные изменения FastAPI backend для двух frontend-приложений

Изменения сделаны поверх `subscription_platform_backend_updated.zip`.

## Изменённые файлы

- `.env.example` — добавлен `CORS_ORIGINS`.
- `app/core/config.py` — типизированная настройка origins и запрет `*` в production.
- `app/main.py` — `CORSMiddleware` для customer/admin origins.
- `app/api/router.py` — подключён системный router.
- `app/api/routes/admin/posts.py` — чтение одной admin-новости по UUID.
- `app/services/post_service.py` — простая операция `get_admin`.
- `app/schemas/deposit.py` — админский ответ нераспознанного депозита дополнен реальными Binance-полями.
- `README.md` и `PROJECT_TREE.md` — документация обновлена.

## Новые файлы

- `app/api/routes/system.py`.
- `app/schemas/system.py`.
- `tests/test_frontend_integration.py`.

## Новые endpoints

```text
GET /api/v1/system/config
GET /api/v1/admin/posts/{post_id}
```

## Миграции

Новые Alembic-миграции не добавлялись: изменения не создают таблицы и не меняют колонки.
