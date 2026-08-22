# Docker Compose на ПК и сервере без конфликтов Git

## Основное правило

`docker-compose.yml` — общий файл проекта и хранится в Git. Его не нужно править отдельно на сервере.

Все значения, которые отличаются между ПК и сервером, задаются в корневом `.env`. Этот файл уже находится в `.gitignore`, поэтому `git pull` его не перезаписывает.

В текущем Compose через `.env` настраиваются:

- host и порты PostgreSQL, API и двух frontend;
- URL API, встраиваемый во frontend;
- политика перезапуска контейнеров;
- DNS-серверы контейнеров;
- PostgreSQL login/password/database.

Начальная настройка на каждой машине:

```bash
cp .env.example .env
nano .env
```

После этого обычный `git pull` обновляет общий Compose, но сохраняет локальные и production-значения в `.env`.

## Когда различается не значение, а структура Compose

Например, только серверу нужны отдельные logging-настройки, дополнительная сеть или volume. Тогда создайте серверный override:

```bash
cp docker-compose.server.example.yml docker-compose.server.yml
```

`docker-compose.server.yml` находится в `.gitignore` и не будет изменён Git.

Запуск:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  up -d --build
```

Проверка итоговой объединённой конфигурации до запуска:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.server.yml \
  config
```

Чтобы не писать `-f` каждый раз на Linux-сервере, можно добавить в `~/.profile`:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.server.yml
```

После нового входа в shell снова достаточно обычных команд:

```bash
docker compose up -d
docker compose logs email-worker --tail=200
```

На Windows разделитель `COMPOSE_FILE` обычно `;`, а не `:`. Поэтому для ПК проще использовать параметры из `.env` либо явные ключи `-f`.

## Что делать с уже изменённым серверным docker-compose.yml

Перед первым переходом сохраните его отличия:

```bash
cp docker-compose.yml docker-compose.server.backup.yml
git diff -- docker-compose.yml
```

Перенесите только серверные значения в `.env`, а структурные отличия — в `docker-compose.server.yml`. После проверки итоговой конфигурации верните общий файл из Git:

```bash
git restore docker-compose.yml
docker compose -f docker-compose.yml -f docker-compose.server.yml config
```

Не используйте `git update-index --skip-worktree docker-compose.yml`: такой флаг скрывает реальные обновления общего Compose и со временем делает серверную конфигурацию непредсказуемой.
