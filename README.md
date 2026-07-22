# Automotive Platform — два frontend-приложения

Рабочая структура:

```text
frontends/
├── customer-frontend/   # клиентский сайт, порт 3000
├── admin-frontend/      # отдельная админ-панель, порт 3001
├── backend/             # FastAPI в полном workspace archive
├── BACKEND_API_MAP.md
├── docker-compose.yml
└── README.md
```

`customer-frontend` и `admin-frontend` — независимые Vite-проекты с собственными `package.json`, TypeScript, тестами, Dockerfile, Nginx и README. Общего runtime bundle и маршрута `/admin` нет.

## Запуск всего набора

В полном workspace сначала подготовьте backend:

```bash
cp backend/.env.example backend/.env
```

Укажите безопасный `JWT_SECRET`. Для запуска без реального Binance:

```env
BINANCE_ENABLED=false
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

Затем:

```bash
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose run --rm api python scripts/create_admin.py
docker compose up --build api deposit-worker reward-worker customer-frontend admin-frontend
```

Адреса:

```text
Клиентский сайт: http://localhost:3000
Админ-панель:    http://localhost:3001
Backend:         http://localhost:8000
Swagger:         http://localhost:8000/docs
```

## Запуск без Docker

Backend запускается отдельно по его README. В двух терминалах:

```bash
cd customer-frontend
cp .env.example .env
npm ci
npm run dev
```

```bash
cd admin-frontend
cp .env.example .env
npm ci
npm run dev
```

## Минимальные изменения backend

Для browser integration добавлены:

1. явный CORS для портов 3000 и 3001;
2. безопасный `/api/v1/system/config` без секретов;
3. чтение admin-новости по UUID для формы редактирования;
4. расширение ответа нераспознанного депозита реальным Binance ID, монетой, временем, Binance-статусом и признаком использованного TxID.

База данных и финансовая модель не изменялись; новой Alembic-миграции нет.

## Проверки

Клиентский проект:

```text
TypeScript: passed
ESLint:     passed
Tests:      18 passed
Build:      passed
npm audit:  0 vulnerabilities
```

Админ-проект:

```text
TypeScript: passed
ESLint:     passed
Tests:      16 passed
Build:      passed
npm audit:  0 vulnerabilities
```

Подробности backend endpoints и отсутствующих API: [BACKEND_API_MAP.md](BACKEND_API_MAP.md).

## Ограничения выполненной проверки

- Docker CLI в среде отсутствовал, поэтому общий Compose проверен статически, без сборки контейнеров.
- Живой PostgreSQL и реальный Binance API не запускались. Backend-тесты выполнены на SQLite, а PostgreSQL DDL Alembic успешно скомпилирован в offline-режиме.
- Существующая миграция `0002` использует PostgreSQL-команду `ALTER COLUMN DROP DEFAULT`; полный upgrade/downgrade-цикл на SQLite поэтому не является поддерживаемым сценарием. Production target проекта — PostgreSQL.
- Deep links обоих production builds проверены через Vite preview. Конфигурация Nginx содержит обязательный React Router fallback.
