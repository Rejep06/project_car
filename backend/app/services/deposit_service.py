"""Уникальные заявки, обработка переводов блокчейна и ручное зачисление."""

import secrets
from datetime import timedelta
from hashlib import sha256
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.enums import (
    BlockchainDepositStatus,
    DepositInvoiceStatus,
    UnmatchedDepositReason,
    UnmatchedDepositStatus,
    WalletOperationType,
)
from app.db.models import (
    BlockchainDeposit,
    DepositAmountReservation,
    DepositInvoice,
    DepositWallet,
    UnmatchedDeposit,
    User,
)
from app.integrations.infura.schemas import BlockchainTransferData
from app.services.audit_service import AuditService
from app.services.deposit_wallet_service import DepositWalletService
from app.services.wallet_service import WalletService
from app.utils.datetime import utcnow
from app.utils.money import ATOMIC_FACTOR, MAX_ATOMIC, format_amount, parse_amount


class DepositService:
    @staticmethod
    async def _existing_request(
        session: AsyncSession, *, user_id: UUID, key: str, fingerprint: str
    ) -> DepositInvoice | None:
        existing = await session.scalar(
            select(DepositInvoice).where(DepositInvoice.request_idempotency_key == key)
        )
        if existing is not None and (
            existing.user_id != user_id or existing.request_fingerprint != fingerprint
        ):
            raise AppError(
                "idempotency_key_conflict",
                "Запрос уже использован для другого пополнения",
                status_code=409,
            )
        return existing

    @staticmethod
    async def expire_invoices(session: AsyncSession) -> int:
        result = await session.execute(
            update(DepositInvoice)
            .where(
                DepositInvoice.status == DepositInvoiceStatus.WAITING,
                DepositInvoice.expires_at < utcnow(),
            )
            .values(status=DepositInvoiceStatus.EXPIRED)
        )
        await session.flush()
        return int(result.rowcount or 0)

    @staticmethod
    async def create_invoice(
        session: AsyncSession,
        *,
        user: User,
        amount: str,
        deposit_wallet_id: UUID | None = None,
        idempotency_key: str | None = None,
        settings: Settings | None = None,
    ) -> DepositInvoice:
        """Резервирует уникальную точную сумму минимум на заданный срок."""
        settings = settings or get_settings()
        # Keep scalar snapshots: SQLAlchemy expires ORM state after a rollback.
        user_id = user.id
        requested_atomic = parse_amount(amount)
        fingerprint = sha256(
            f"{requested_atomic}:{deposit_wallet_id or 'default'}".encode()
        ).hexdigest()
        if idempotency_key is not None:
            await WalletService.lock_wallet(session, user_id)
            existing = await DepositService._existing_request(
                session, user_id=user_id, key=idempotency_key, fingerprint=fingerprint
            )
            if existing is not None:
                return existing
        if user.is_frozen:
            raise AppError("user_frozen", "Операции пользователя заморожены", status_code=403)
        deposit_wallet = await DepositWalletService.get_active(
            session, deposit_wallet_id, settings
        )
        if requested_atomic < settings.min_deposit_amount_atomic:
            raise AppError(
                "deposit_amount_too_small",
                f"Минимальная сумма пополнения: {settings.min_deposit_amount}",
                status_code=409,
            )
        if requested_atomic > MAX_ATOMIC - 999_000:
            raise AppError(
                "deposit_amount_too_large",
                "Сумма пополнения превышает допустимый диапазон",
                status_code=409,
            )

        wallet_id = deposit_wallet.id
        wallet_asset = deposit_wallet.asset
        wallet_network = deposit_wallet.network
        wallet_address = deposit_wallet.address
        for _attempt in range(10):
            if idempotency_key is not None:
                # Reacquire after a reservation uniqueness rollback. The wallet
                # row serializes concurrent requests for one user on PostgreSQL.
                await WalletService.lock_wallet(session, user_id)
                existing = await DepositService._existing_request(
                    session, user_id=user_id, key=idempotency_key, fingerprint=fingerprint
                )
                if existing is not None:
                    return existing
            now = utcnow()
            await session.execute(
                delete(DepositAmountReservation).where(
                    DepositAmountReservation.reserved_until <= now
                )
            )
            reserved = set(
                (
                    await session.scalars(
                        select(DepositAmountReservation.expected_amount_atomic)
                    )
                ).all()
            )
            codes = list(range(1, 1000))
            secrets.SystemRandom().shuffle(codes)
            expected_atomic = next(
                (
                    requested_atomic + code * 1000
                    for code in codes
                    if requested_atomic + code * 1000 not in reserved
                ),
                None,
            )
            if expected_atomic is None:
                await session.rollback()
                raise AppError(
                    "deposit_amount_pool_exhausted",
                    "Не удалось подобрать уникальную сумму. Повторите позже",
                    status_code=503,
                )

            expires_at = now + timedelta(minutes=settings.deposit_invoice_ttl_minutes)
            reserved_until = max(
                now + timedelta(hours=settings.deposit_amount_reservation_hours),
                expires_at + timedelta(hours=1),
            )
            invoice = DepositInvoice(
                user_id=user_id,
                requested_amount_atomic=requested_atomic,
                request_idempotency_key=idempotency_key,
                request_fingerprint=fingerprint if idempotency_key else None,
                expected_amount_atomic=expected_atomic,
                deposit_wallet_id=wallet_id,
                asset=wallet_asset,
                network=wallet_network,
                deposit_address=wallet_address,
                status=DepositInvoiceStatus.WAITING,
                expires_at=expires_at,
                amount_reserved_until=reserved_until,
            )
            reservation = DepositAmountReservation(
                invoice=invoice,
                expected_amount_atomic=expected_atomic,
                reserved_until=reserved_until,
            )
            session.add_all([invoice, reservation])
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                continue
            await session.refresh(invoice)
            return invoice
        raise AppError(
            "deposit_amount_allocation_conflict",
            "Не удалось зарезервировать уникальную сумму из-за конкурирующих запросов",
            status_code=503,
        )

    @staticmethod
    async def list_user_invoices(
        session: AsyncSession,
        *,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[DepositInvoice], int]:
        await DepositService.expire_invoices(session)
        await session.commit()
        condition = DepositInvoice.user_id == user_id
        items = list(
            (
                await session.scalars(
                    select(DepositInvoice)
                    .where(condition)
                    .order_by(DepositInvoice.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(DepositInvoice).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def get_user_invoice(
        session: AsyncSession, *, user_id: UUID, invoice_id: UUID
    ) -> DepositInvoice:
        await DepositService.expire_invoices(session)
        await session.commit()
        invoice = await session.scalar(
            select(DepositInvoice).where(
                DepositInvoice.id == invoice_id,
                DepositInvoice.user_id == user_id,
            )
        )
        if invoice is None:
            raise AppError(
                "deposit_invoice_not_found", "Заявка на пополнение не найдена", status_code=404
            )
        return invoice

    @staticmethod
    def is_target_deposit(data: BlockchainTransferData, wallet: DepositWallet) -> bool:
        """Дополнительно проверяет, что событие относится к настройкам кошелька."""
        expected_contract = (wallet.token_contract_address or "").lower()
        actual_contract = (data.token_contract_address or "").lower()
        return (
            data.status == BlockchainDepositStatus.SUCCESS
            and data.asset == wallet.asset.upper()
            and data.network == wallet.network.upper()
            and data.provider == wallet.provider.lower()
            and data.address.lower() == wallet.address.lower()
            and actual_contract == expected_contract
            and data.confirmations >= wallet.confirmations_required
        )

    @staticmethod
    async def _unmatched_reason(
        session: AsyncSession, data: BlockchainTransferData
    ) -> UnmatchedDepositReason:
        exact_invoice = await session.scalar(
            select(DepositInvoice.id).where(
                DepositInvoice.expected_amount_atomic == data.amount_atomic,
                func.lower(DepositInvoice.deposit_address) == data.address.lower(),
                DepositInvoice.network == data.network,
                DepositInvoice.asset == data.asset,
                DepositInvoice.created_at <= data.detected_at,
                DepositInvoice.amount_reserved_until < data.detected_at,
            )
        )
        if exact_invoice is not None:
            return UnmatchedDepositReason.EXPIRED_INVOICE

        nearby = await session.scalar(
            select(DepositInvoice.id).where(
                DepositInvoice.status.in_(
                    [
                        DepositInvoiceStatus.WAITING,
                        DepositInvoiceStatus.DETECTED,
                        DepositInvoiceStatus.EXPIRED,
                    ]
                ),
                func.lower(DepositInvoice.deposit_address) == data.address.lower(),
                DepositInvoice.network == data.network,
                DepositInvoice.asset == data.asset,
                DepositInvoice.created_at <= data.detected_at,
                DepositInvoice.amount_reserved_until >= data.detected_at,
                DepositInvoice.expected_amount_atomic.between(
                    data.amount_atomic - (ATOMIC_FACTOR - 1),
                    data.amount_atomic + (ATOMIC_FACTOR - 1),
                ),
            )
        )
        if nearby is not None:
            return UnmatchedDepositReason.WRONG_AMOUNT
        return UnmatchedDepositReason.INVOICE_NOT_FOUND

    @staticmethod
    async def process_blockchain_deposit(
        session: AsyncSession,
        *,
        data: BlockchainTransferData,
    ) -> tuple[BlockchainDeposit, bool]:
        """Сохраняет событие и один раз зачисляет фактически полученную сумму."""
        existing = await session.scalar(
            select(BlockchainDeposit).where(
                or_(
                    BlockchainDeposit.external_id == data.external_id,
                    (
                        (BlockchainDeposit.network == data.network)
                        & (BlockchainDeposit.txid == data.txid)
                        & (BlockchainDeposit.log_index == data.log_index)
                    ),
                )
            )
        )
        if existing is not None:
            return existing, False

        deposit = BlockchainDeposit(
            external_id=data.external_id,
            txid=data.txid,
            log_index=data.log_index,
            block_number=data.block_number,
            block_hash=data.block_hash,
            from_address=data.from_address,
            address=data.address,
            asset=data.asset,
            network=data.network,
            provider=data.provider,
            token_contract_address=data.token_contract_address,
            amount_atomic=data.amount_atomic,
            status=data.status,
            confirmations=data.confirmations,
            detected_at=data.detected_at,
            raw_data=data.raw_data,
        )
        session.add(deposit)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            existing = await session.scalar(
                select(BlockchainDeposit).where(
                    or_(
                        BlockchainDeposit.external_id == data.external_id,
                        (
                            (BlockchainDeposit.network == data.network)
                            & (BlockchainDeposit.txid == data.txid)
                            & (BlockchainDeposit.log_index == data.log_index)
                        ),
                    )
                )
            )
            if existing is not None:
                return existing, False
            raise AppError(
                "deposit_uniqueness_conflict",
                "Конфликт уникальности входящего перевода",
                status_code=409,
            ) from exc

        candidates = list(
            (
                await session.scalars(
                    select(DepositInvoice)
                    .where(
                        DepositInvoice.expected_amount_atomic == data.amount_atomic,
                        func.lower(DepositInvoice.deposit_address) == data.address.lower(),
                        DepositInvoice.network == data.network,
                        DepositInvoice.asset == data.asset,
                        DepositInvoice.created_at <= data.detected_at,
                        DepositInvoice.status.in_(
                            [
                                DepositInvoiceStatus.WAITING,
                                DepositInvoiceStatus.DETECTED,
                                DepositInvoiceStatus.EXPIRED,
                            ]
                        ),
                        DepositInvoice.amount_reserved_until >= data.detected_at,
                    )
                    .with_for_update(of=DepositInvoice)
                )
            ).all()
        )
        if len(candidates) == 1:
            invoice = candidates[0]
            deposit.deposit_invoice_id = invoice.id
            invoice.matched_blockchain_deposit_id = deposit.id
            invoice.status = DepositInvoiceStatus.DETECTED
            await WalletService.apply_change(
                session,
                user_id=invoice.user_id,
                operation_type=WalletOperationType.DEPOSIT_CREDIT,
                available_delta_atomic=data.amount_atomic,
                locked_delta_atomic=0,
                idempotency_key=f"deposit:blockchain:{data.external_id}",
                related_entity_type="blockchain_deposit",
                related_entity_id=deposit.id,
                description="Пополнение баланса USDT",
                metadata_json={
                    "txid": data.txid,
                    "log_index": data.log_index,
                    "invoice_id": str(invoice.id),
                    "network": data.network,
                },
            )
            credited_at = utcnow()
            deposit.credited_at = credited_at
            invoice.received_amount_atomic = data.amount_atomic
            invoice.status = DepositInvoiceStatus.CREDITED
            invoice.credited_at = credited_at
            invoice.credited_after_expiration = (
                data.detected_at.replace(tzinfo=None) > invoice.expires_at.replace(tzinfo=None)
            )
            await session.commit()
            return deposit, True

        reason = (
            UnmatchedDepositReason.DUPLICATE_CANDIDATE
            if len(candidates) > 1
            else await DepositService._unmatched_reason(session, data)
        )
        unmatched = UnmatchedDeposit(
            blockchain_deposit_id=deposit.id,
            txid=data.txid,
            amount_atomic=data.amount_atomic,
            address=data.address,
            network=data.network,
            reason=reason,
            status=UnmatchedDepositStatus.UNRESOLVED,
            created_at=utcnow(),
        )
        session.add(unmatched)
        await session.commit()
        return deposit, False

    @staticmethod
    async def list_unmatched(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[UnmatchedDeposit], int]:
        items = list(
            (
                await session.scalars(
                    select(UnmatchedDeposit)
                    .options(joinedload(UnmatchedDeposit.blockchain_deposit))
                    .order_by(UnmatchedDeposit.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).unique().all()
        )
        total = int(
            await session.scalar(select(func.count()).select_from(UnmatchedDeposit)) or 0
        )
        return items, total

    @staticmethod
    async def get_unmatched(session: AsyncSession, unmatched_id: UUID) -> UnmatchedDeposit:
        item = await session.scalar(
            select(UnmatchedDeposit)
            .options(joinedload(UnmatchedDeposit.blockchain_deposit))
            .where(UnmatchedDeposit.id == unmatched_id)
        )
        if item is None:
            raise AppError(
                "unmatched_deposit_not_found",
                "Нераспознанный депозит не найден",
                status_code=404,
            )
        return item

    @staticmethod
    async def assign_unmatched(
        session: AsyncSession,
        *,
        unmatched_id: UUID,
        user_id: UUID,
        invoice_id: UUID | None,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> UnmatchedDeposit:
        item = await session.scalar(
            select(UnmatchedDeposit)
            .options(joinedload(UnmatchedDeposit.blockchain_deposit))
            .where(UnmatchedDeposit.id == unmatched_id)
            .with_for_update(of=UnmatchedDeposit)
        )
        if item is None:
            raise AppError(
                "unmatched_deposit_not_found",
                "Нераспознанный депозит не найден",
                status_code=404,
            )
        if item.status == UnmatchedDepositStatus.IGNORED:
            raise AppError(
                "unmatched_deposit_ignored",
                "Депозит помечен как игнорируемый",
                status_code=409,
            )
        if item.status == UnmatchedDepositStatus.ASSIGNED:
            if item.assigned_user_id == user_id and item.assigned_invoice_id == invoice_id:
                return item
            raise AppError("deposit_already_assigned", "Депозит уже назначен", status_code=409)

        user = await session.get(User, user_id)
        if user is None:
            raise AppError("user_not_found", "Пользователь не найден", status_code=404)
        invoice: DepositInvoice | None = None
        if invoice_id is not None:
            invoice = await session.scalar(
                select(DepositInvoice)
                .where(DepositInvoice.id == invoice_id)
                .with_for_update(of=DepositInvoice)
            )
            if invoice is None:
                raise AppError(
                    "deposit_invoice_not_found",
                    "Заявка на пополнение не найдена",
                    status_code=404,
                )
            if invoice.user_id != user_id:
                raise AppError(
                    "invoice_owner_mismatch",
                    "Заявка принадлежит другому пользователю",
                    status_code=409,
                )
            if (
                invoice.status == DepositInvoiceStatus.CREDITED
                and invoice.matched_blockchain_deposit_id != item.blockchain_deposit_id
            ):
                raise AppError(
                    "invoice_already_credited",
                    "Заявка уже зачислена другим депозитом",
                    status_code=409,
                )

        deposit = item.blockchain_deposit
        if deposit.credited_at is not None and deposit.deposit_invoice_id != invoice_id:
            raise AppError(
                "deposit_already_credited", "Депозит уже был зачислен", status_code=409
            )

        transaction, created = await WalletService.apply_change(
            session,
            user_id=user_id,
            operation_type=WalletOperationType.DEPOSIT_CREDIT,
            available_delta_atomic=item.amount_atomic,
            locked_delta_atomic=0,
            idempotency_key=f"manual-deposit:{deposit.external_id}",
            related_entity_type="blockchain_deposit",
            related_entity_id=deposit.id,
            description="Ручное зачисление проблемного депозита",
            metadata_json={"txid": item.txid, "admin_user_id": str(admin_user_id)},
        )
        assigned_at = utcnow()
        item.status = UnmatchedDepositStatus.ASSIGNED
        item.assigned_user_id = user_id
        item.assigned_invoice_id = invoice_id
        item.assigned_by_admin_id = admin_user_id
        item.assigned_at = assigned_at
        deposit.deposit_invoice_id = invoice_id
        deposit.credited_at = deposit.credited_at or assigned_at
        if invoice is not None:
            invoice.matched_blockchain_deposit_id = deposit.id
            invoice.received_amount_atomic = item.amount_atomic
            invoice.status = DepositInvoiceStatus.CREDITED
            invoice.credited_at = invoice.credited_at or assigned_at
        if created:
            await AuditService.record(
                session,
                admin_user_id=admin_user_id,
                action="manual_deposit_credited",
                entity_type="unmatched_deposit",
                entity_id=item.id,
                new_data={
                    "user_id": str(user_id),
                    "invoice_id": str(invoice_id) if invoice_id else None,
                    "amount": format_amount(item.amount_atomic),
                    "txid": item.txid,
                    "wallet_transaction_id": str(transaction.id),
                },
                ip_address=ip_address,
            )
        await session.commit()
        return await DepositService.get_unmatched(session, item.id)

    @staticmethod
    async def ignore_unmatched(
        session: AsyncSession,
        *,
        unmatched_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> UnmatchedDeposit:
        item = await session.scalar(
            select(UnmatchedDeposit)
            .where(UnmatchedDeposit.id == unmatched_id)
            .with_for_update(of=UnmatchedDeposit)
        )
        if item is None:
            raise AppError(
                "unmatched_deposit_not_found",
                "Нераспознанный депозит не найден",
                status_code=404,
            )
        if item.status == UnmatchedDepositStatus.ASSIGNED:
            raise AppError(
                "deposit_already_assigned",
                "Зачисленный депозит нельзя игнорировать",
                status_code=409,
            )
        item.status = UnmatchedDepositStatus.IGNORED
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="unmatched_deposit_ignored",
            entity_type="unmatched_deposit",
            entity_id=item.id,
            new_data={"txid": item.txid},
            ip_address=ip_address,
        )
        await session.commit()
        return await DepositService.get_unmatched(session, item.id)

    @staticmethod
    async def find_by_txid(
        session: AsyncSession, txid: str
    ) -> tuple[BlockchainDeposit | None, UnmatchedDeposit | None]:
        deposit = await session.scalar(
            select(BlockchainDeposit)
            .options(joinedload(BlockchainDeposit.deposit_invoice))
            .where(BlockchainDeposit.txid == txid)
            .order_by(BlockchainDeposit.log_index)
        )
        unmatched = await session.scalar(
            select(UnmatchedDeposit)
            .options(joinedload(UnmatchedDeposit.blockchain_deposit))
            .where(UnmatchedDeposit.txid == txid)
            .order_by(UnmatchedDeposit.created_at)
        )
        return deposit, unmatched
