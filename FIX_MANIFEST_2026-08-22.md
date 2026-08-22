# Исправления от 22 августа 2026 года

## Email worker

- Добавлена валидация и нормализация `SMTP_HOST`.
- Добавлена отдельная DNS-проверка `python -m app.workers.email_worker --check`.
- Добавлен Docker healthcheck для `email-worker`.
- При недоступном SMTP DNS worker приостанавливает выборку новых писем.
- DNS-сбой не расходует `attempt_count`, даже если произошёл между проверкой и отправкой.
- Добавлен скрипт возврата исчерпавших попытки писем:
  `backend/scripts/requeue_failed_emails.py`.
- Добавлены целевые тесты SMTP/DNS.

## Главная страница

- На главную добавлен блок «Актуальные лотереи».
- Показывается до трёх публичных лотерей с приоритетом открытых продаж.
- Карточка вынесена в `customer-frontend/src/components/LotteryCard.tsx` и
  переиспользуется в каталоге.
- Добавлен frontend-тест лотереи на главной.

## Docker Compose

- Машинно-зависимые значения параметризованы через корневой `.env`.
- Добавлены настраиваемые DNS-серверы backend-контейнеров.
- Добавлен пример игнорируемого server override.
- Добавлены инструкции `COMPOSE_ENVIRONMENTS.md` и
  `DEPLOY_DNS_LOTTERY_FIX.md`.

## Проверки

- SMTP/DNS unit tests: 7/7.
- Python `compileall`: успешно.
- TypeScript/TSX syntax parse: 143 non-declaration файла, ошибок нет.
- Три Compose YAML-файла разобраны успешно.
- Полный `pytest`, Vitest, production build и реальный Docker Compose не
  запускались из-за ограничений проверочного окружения; подробности находятся
  в `VALIDATION_REPORT.md`.

## Секреты

Архив с исправленным workspace не содержит `.env`, `.git`, виртуальное
окружение, кэши, `node_modules` и build-артефакты. Файлы `.env.example`
сохранены.
