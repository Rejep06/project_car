# Настройка пополнений USDT ERC-20 через Infura

## Что проверяет система

Текущая автоматическая интеграция отслеживает входящие переводы:

```text
Блокчейн: Ethereum Mainnet
Актив:    USDT
Стандарт: ERC-20
Контракт: 0xdac17f958d2ee523a2206206994597c13d831ec7
Провайдер: Infura Ethereum JSON-RPC
```

Worker читает события `Transfer` контракта USDT, адресованные активным кошелькам из таблицы `deposit_wallets`.

## 1. Создание Infura API key

Создайте проект Ethereum в Infura и получите API key. В `backend/.env` укажите:

```env
DEPOSIT_MONITORING_ENABLED=true
INFURA_API_KEY=ваш-api-key
ETHEREUM_PROVIDER_NETWORK=mainnet
ETHEREUM_CHAIN_ID=1
```

Стандартный endpoint формируется автоматически:

```text
https://mainnet.infura.io/v3/<INFURA_API_KEY>
```

Если используется собственный endpoint или отдельный Infura endpoint, задайте полный URL:

```env
INFURA_RPC_URL=https://...
```

При заполненном `INFURA_RPC_URL` URL из `INFURA_API_KEY` не формируется.

Необязательный JWT для защищённого endpoint:

```env
INFURA_JWT=
```

## 2. Параметры USDT

```env
ASSET=USDT
ASSET_DECIMALS=6
NETWORK=ETHEREUM
NETWORK_DISPLAY_NAME=Ethereum (ERC-20)
ETHEREUM_USDT_CONTRACT_ADDRESS=0xdac17f958d2ee523a2206206994597c13d831ec7
ETHEREUM_USDT_DECIMALS=6
ETHEREUM_CONFIRMATIONS=12
```

Не заменяйте контракт произвольным токеном с названием USDT. Автоматическая проверка должна быть привязана к официальному контракту Tether в Ethereum.

## 3. Добавление адреса

Адрес можно добавить двумя способами.

### Через админ-панель

Откройте **«Адреса пополнения» → «Добавить адрес»** и заполните:

```text
Название: Основной Ethereum кошелёк
Адрес: 0x...
Актив: USDT
Код сети: ETHEREUM
Название сети: Ethereum (ERC-20)
Автоматическая проверка: включена
Провайдер: Infura
Сеть Infura: mainnet
Chain ID: 1
Стандарт: ERC20
Контракт: 0xdac17f958d2ee523a2206206994597c13d831ec7
Знаков токена: 6
Подтверждений: 12
```

### Через `.env`

Если в базе ещё нет кошельков:

```env
DEFAULT_DEPOSIT_ADDRESS=0x...
```

При первом обращении backend создаст основной адрес в БД. После этого реквизитами лучше управлять через админ-панель.

## 4. Диапазоны сканирования

```env
DEPOSIT_POLL_INTERVAL_SECONDS=20
ETHEREUM_INITIAL_LOOKBACK_BLOCKS=7200
ETHEREUM_REORG_LOOKBACK_BLOCKS=24
ETHEREUM_LOG_BLOCK_RANGE=1000
ETHEREUM_ADDRESS_BATCH_SIZE=50
```

- `INITIAL_LOOKBACK_BLOCKS` — сколько предыдущих блоков проверить при первом запуске;
- `REORG_LOOKBACK_BLOCKS` — сколько уже просмотренных блоков пересканировать;
- `LOG_BLOCK_RANGE` — размер одного запроса `eth_getLogs`;
- `ADDRESS_BATCH_SIZE` — сколько адресов передавать в одном фильтре событий.

Состояние сканирования сохраняется в таблице `blockchain_sync_states`, поэтому перезапуск worker не начинает полное сканирование заново.

## 5. Миграция и запуск

Из корня проекта:

```bash
docker compose build api deposit-worker reward-worker
docker compose up -d db
docker compose run --rm api alembic upgrade head
docker compose up -d api deposit-worker reward-worker
```

Проверка:

```bash
docker compose ps
docker compose logs -f deposit-worker
```

Нормальный worker пишет сообщение о запуске и затем работает циклами. При найденном и зачисленном переводе появляется количество обработанных пополнений.

## 6. Адреса других сетей

Администратор может сохранить адрес любой сети. Для неподдерживаемой сети:

```text
Автоматическая проверка: выключена
Провайдер: manual
```

Текущая версия автоматически сканирует только Ethereum Mainnet / USDT ERC-20 / Infura. Для Solana, BNB Chain, Polygon, Tron и других сетей необходимо отдельно реализовать адаптер провайдера и правила подтверждений.

## 7. Безопасность

- Для чтения входящих переводов приватный ключ кошелька не нужен.
- Не храните seed phrase или приватный ключ в `.env` проекта.
- Infura API key и JWT не передаются клиентскому frontend.
- PostgreSQL не должен публиковаться в интернет.
- Перед миграцией production-базы сделайте резервную копию.
- Используйте отдельные адреса и ключи для тестовой и production-среды.
