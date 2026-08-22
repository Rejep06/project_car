"""Периодическая проверка входящих USDT ERC-20 переводов через Infura."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.models import BlockchainSyncState, DepositWallet
from app.db.session import async_session_maker
from app.integrations.infura.client import InfuraEthereumClient
from app.services.deposit_service import DepositService
from app.services.deposit_wallet_service import DepositWalletService

logger = logging.getLogger(__name__)

ClientFactory = Callable[[Settings, str], InfuraEthereumClient]


def _default_client_factory(settings: Settings, provider_network: str) -> InfuraEthereumClient:
    return InfuraEthereumClient(settings, provider_network=provider_network)


def _group_key(wallet: DepositWallet) -> tuple[Any, ...]:
    return (
        wallet.provider.lower(),
        (wallet.provider_network or "").lower(),
        wallet.chain_id,
        wallet.network.upper(),
        wallet.asset.upper(),
        (wallet.token_contract_address or "").lower(),
        wallet.token_decimals,
        wallet.confirmations_required,
    )


def _sync_key(group: tuple[Any, ...]) -> str:
    return ":".join(str(item) for item in group)


async def _get_or_create_sync_state(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    group: tuple[Any, ...],
    initial_block: int,
) -> BlockchainSyncState:
    provider, provider_network, chain_id, network, _, contract, _, _ = group
    key = _sync_key(group)
    async with session_factory() as session:
        state = await session.scalar(
            select(BlockchainSyncState).where(BlockchainSyncState.sync_key == key)
        )
        if state is None:
            state = BlockchainSyncState(
                sync_key=key,
                provider=provider,
                provider_network=provider_network,
                chain_id=int(chain_id),
                network=network,
                token_contract_address=contract,
                last_scanned_block=initial_block,
            )
            session.add(state)
            await session.commit()
            await session.refresh(state)
        return state


async def _save_sync_block(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    sync_key: str,
    block_number: int,
) -> None:
    async with session_factory() as session:
        state = await session.scalar(
            select(BlockchainSyncState)
            .where(BlockchainSyncState.sync_key == sync_key)
            .with_for_update(of=BlockchainSyncState)
        )
        if state is None:
            raise RuntimeError("Состояние сканирования не найдено")
        state.last_scanned_block = max(state.last_scanned_block, block_number)
        await session.commit()


async def run_deposit_cycle(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    client_factory: ClientFactory | None = None,
) -> int:
    """Сканирует подтверждённые ERC-20 события и зачисляет подходящие заявки."""
    if not settings.deposit_monitoring_enabled:
        return 0

    async with session_factory() as session:
        await DepositService.expire_invoices(session)
        wallets = await DepositWalletService.list_monitorable(session, settings)
        await session.commit()
    if not wallets:
        return 0

    groups: dict[tuple[Any, ...], list[DepositWallet]] = defaultdict(list)
    for wallet in wallets:
        if wallet.provider.lower() != "infura":
            logger.warning(
                "Пропущен кошелёк %s: провайдер %s пока не поддерживается",
                wallet.id,
                wallet.provider,
            )
            continue
        if (wallet.token_standard or "").upper() != "ERC20":
            logger.warning("Пропущен кошелёк %s: поддерживается только ERC-20", wallet.id)
            continue
        groups[_group_key(wallet)].append(wallet)

    factory = client_factory or _default_client_factory
    credited_count = 0
    for group, group_wallets in groups.items():
        (
            provider,
            provider_network,
            chain_id,
            network,
            asset,
            contract,
            _token_decimals,
            confirmations_required,
        ) = group
        client = factory(settings, provider_network)
        try:
            actual_chain_id = await client.get_chain_id()
            if actual_chain_id != chain_id:
                raise AppError(
                    "infura_chain_mismatch",
                    f"Infura подключён к chain ID {actual_chain_id}, ожидался {chain_id}",
                    status_code=503,
                )
            latest_block = await client.get_block_number()
            safe_head = (
                latest_block
                if confirmations_required <= 1
                else latest_block - confirmations_required + 1
            )
            if safe_head < 0:
                continue

            state = await _get_or_create_sync_state(
                session_factory,
                group=group,
                initial_block=max(0, safe_head - settings.ethereum_initial_lookback_blocks),
            )
            from_block = max(
                0,
                state.last_scanned_block - settings.ethereum_reorg_lookback_blocks + 1,
            )
            addresses = sorted({wallet.address.lower() for wallet in group_wallets})
            wallets_by_address = {wallet.address.lower(): wallet for wallet in group_wallets}
            sync_key = _sync_key(group)

            range_start = from_block
            while range_start <= safe_head:
                range_end = min(
                    safe_head,
                    range_start + settings.ethereum_log_block_range - 1,
                )
                for offset in range(0, len(addresses), settings.ethereum_address_batch_size):
                    batch = addresses[offset : offset + settings.ethereum_address_batch_size]
                    logs = await client.get_erc20_transfer_logs(
                        contract_address=contract,
                        recipient_addresses=batch,
                        from_block=range_start,
                        to_block=range_end,
                    )
                    transfers = await client.normalize_erc20_transfers(
                        logs=logs,
                        latest_block=latest_block,
                        asset=asset,
                        network=network,
                        token_contract_address=contract,
                    )
                    for data in sorted(
                        transfers, key=lambda item: (item.block_number, item.log_index)
                    ):
                        wallet = wallets_by_address.get(data.address.lower())
                        if wallet is None or not DepositService.is_target_deposit(data, wallet):
                            continue
                        async with session_factory() as session:
                            _, credited = await DepositService.process_blockchain_deposit(
                                session, data=data
                            )
                            if credited:
                                credited_count += 1
                await _save_sync_block(
                    session_factory, sync_key=sync_key, block_number=range_end
                )
                range_start = range_end + 1
        finally:
            await client.close()
    return credited_count


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Обработчик пополнений Ethereum/Infura запущен")
    while True:
        try:
            processed = await run_deposit_cycle(
                session_factory=async_session_maker,
                settings=settings,
            )
            if processed:
                logger.info("Зачислено пополнений: %s", processed)
        except Exception:
            logger.exception("Ошибка цикла обработки пополнений")
        await asyncio.sleep(settings.deposit_poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
