"""Управление несколькими адресами пополнения."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.models import DepositWallet
from app.schemas.deposit_wallet import DepositWalletCreate, DepositWalletUpdate
from app.services.audit_service import AuditService


WALLET_FIELDS = tuple(DepositWalletCreate.model_fields)


def wallet_snapshot(wallet: DepositWallet) -> dict[str, Any]:
    return {field: getattr(wallet, field) for field in WALLET_FIELDS}


class DepositWalletService:
    @staticmethod
    async def ensure_default_wallet(
        session: AsyncSession, settings: Settings | None = None
    ) -> None:
        """Переносит адрес по умолчанию из env в БД, если адресов ещё нет."""
        settings = settings or get_settings()
        total = int(
            await session.scalar(select(func.count()).select_from(DepositWallet)) or 0
        )
        if total or not settings.default_deposit_address.strip():
            return
        payload = DepositWalletCreate(
            title="Основной кошелёк",
            asset=settings.asset,
            network=settings.network,
            network_display_name=settings.network_display_name,
            address=settings.default_deposit_address,
            provider="infura",
            provider_network=settings.ethereum_provider_network,
            chain_id=settings.ethereum_chain_id,
            token_standard="ERC20",
            token_contract_address=settings.ethereum_usdt_contract_address,
            token_decimals=settings.ethereum_usdt_decimals,
            confirmations_required=settings.ethereum_confirmations,
            monitoring_enabled=True,
            is_active=True,
            sort_order=0,
        )
        session.add(DepositWallet(**payload.model_dump()))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()

    @classmethod
    async def list_active(
        cls, session: AsyncSession, settings: Settings | None = None
    ) -> list[DepositWallet]:
        await cls.ensure_default_wallet(session, settings)
        return list(
            (
                await session.scalars(
                    select(DepositWallet)
                    .where(DepositWallet.is_active.is_(True))
                    .order_by(DepositWallet.sort_order, DepositWallet.created_at)
                )
            ).all()
        )

    @classmethod
    async def list_monitorable(
        cls, session: AsyncSession, settings: Settings | None = None
    ) -> list[DepositWallet]:
        await cls.ensure_default_wallet(session, settings)
        return list(
            (
                await session.scalars(
                    select(DepositWallet)
                    .where(
                        DepositWallet.is_active.is_(True),
                        DepositWallet.monitoring_enabled.is_(True),
                    )
                    .order_by(DepositWallet.sort_order, DepositWallet.created_at)
                )
            ).all()
        )

    @classmethod
    async def get_active(
        cls,
        session: AsyncSession,
        wallet_id: UUID | None,
        settings: Settings | None = None,
    ) -> DepositWallet:
        wallets = await cls.list_active(session, settings)
        if not wallets:
            raise AppError(
                "deposit_address_not_configured",
                "Адреса пополнения временно недоступны",
                status_code=503,
            )
        if wallet_id is None:
            return wallets[0]
        wallet = next((item for item in wallets if item.id == wallet_id), None)
        if wallet is None:
            raise AppError(
                "deposit_wallet_not_found",
                "Выбранный адрес пополнения недоступен",
                status_code=404,
            )
        return wallet

    @staticmethod
    async def list_admin(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[DepositWallet], int]:
        items = list(
            (
                await session.scalars(
                    select(DepositWallet)
                    .order_by(DepositWallet.sort_order, DepositWallet.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(select(func.count()).select_from(DepositWallet)) or 0
        )
        return items, total

    @staticmethod
    async def get_admin(session: AsyncSession, wallet_id: UUID) -> DepositWallet:
        wallet = await session.get(DepositWallet, wallet_id)
        if wallet is None:
            raise AppError(
                "deposit_wallet_not_found", "Адрес пополнения не найден", status_code=404
            )
        return wallet

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        data: DepositWalletCreate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> DepositWallet:
        wallet = DepositWallet(**data.model_dump())
        session.add(wallet)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError(
                "deposit_wallet_exists", "Такой адрес уже добавлен", status_code=409
            ) from exc
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="deposit_wallet_created",
            entity_type="deposit_wallet",
            entity_id=wallet.id,
            new_data=wallet_snapshot(wallet),
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(wallet)
        return wallet

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        wallet_id: UUID,
        data: DepositWalletUpdate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> DepositWallet:
        wallet = await session.scalar(
            select(DepositWallet)
            .where(DepositWallet.id == wallet_id)
            .with_for_update(of=DepositWallet)
        )
        if wallet is None:
            raise AppError(
                "deposit_wallet_not_found", "Адрес пополнения не найден", status_code=404
            )
        old_data = wallet_snapshot(wallet)
        merged = {**old_data, **data.model_dump(exclude_unset=True)}
        validated = DepositWalletCreate.model_validate(merged)
        for field, value in validated.model_dump().items():
            setattr(wallet, field, value)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError(
                "deposit_wallet_exists", "Такой адрес уже добавлен", status_code=409
            ) from exc
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="deposit_wallet_updated",
            entity_type="deposit_wallet",
            entity_id=wallet.id,
            old_data=old_data,
            new_data=wallet_snapshot(wallet),
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(wallet)
        return wallet
