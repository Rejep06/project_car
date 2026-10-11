"""Заявки на ручной вывод и перенос средств между available/locked."""

from datetime import datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.enums import WalletOperationType, WithdrawalStatus
from app.db.models import User, WithdrawalRequest
from app.services.audit_service import AuditService
from app.services.wallet_service import WalletService
from app.utils.datetime import ensure_utc, get_withdrawal_window, utcnow
from app.utils.money import MAX_ATOMIC, format_amount, parse_amount, percentage_fee


class WithdrawalService:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user: User,
        destination_address: str,
        amount: str,
        settings: Settings | None = None,
    ) -> WithdrawalRequest:
        settings = settings or get_settings()
        if user.is_frozen:
            raise AppError("user_frozen", "Операции пользователя временно недоступны", status_code=403)
        window = get_withdrawal_window(
            timezone_name=settings.business_timezone,
            allowed_weekday=settings.withdrawal_allowed_weekday,
        )
        if not window.is_open:
            next_date = (
                window.next_open_at.astimezone(window.local_now.tzinfo).strftime("%d.%m.%Y")
                if window.next_open_at is not None
                else "в следующую среду"
            )
            raise AppError(
                "withdrawal_day_closed",
                f"Заявку на вывод можно подать каждую среду. Ближайшая дата: {next_date}",
                status_code=409,
            )
        amount_atomic = parse_amount(amount)
        if amount_atomic < settings.min_withdrawal_amount_atomic:
            raise AppError(
                "withdrawal_amount_too_small",
                f"Минимальная сумма вывода: {settings.min_withdrawal_amount}",
                status_code=409,
            )
        fee_atomic = percentage_fee(amount_atomic, settings.withdrawal_fee_percent)
        total_atomic = amount_atomic + fee_atomic
        if total_atomic > MAX_ATOMIC:
            raise AppError(
                "withdrawal_amount_too_large",
                "Сумма вывода превышает допустимый диапазон",
                status_code=409,
            )
        withdrawal = WithdrawalRequest(
            id=uuid4(),
            user_id=user.id,
            asset=settings.asset,
            network=settings.network,
            destination_address=destination_address,
            amount_atomic=amount_atomic,
            fee_atomic=fee_atomic,
            total_debit_atomic=total_atomic,
            status=WithdrawalStatus.PENDING_REVIEW,
        )
        await WalletService.apply_change(
            session,
            user_id=user.id,
            operation_type=WalletOperationType.WITHDRAWAL_HOLD,
            available_delta_atomic=-total_atomic,
            locked_delta_atomic=total_atomic,
            idempotency_key=f"withdrawal:hold:{withdrawal.id}",
            related_entity_type="withdrawal_request",
            related_entity_id=withdrawal.id,
            description="Блокировка средств для заявки на вывод",
            metadata_json={"destination_address": destination_address},
        )
        session.add(withdrawal)
        await session.commit()
        await session.refresh(withdrawal)
        return withdrawal

    @staticmethod
    async def list_user(
        session: AsyncSession, *, user_id: UUID, offset: int, limit: int
    ) -> tuple[list[WithdrawalRequest], int]:
        condition = WithdrawalRequest.user_id == user_id
        items = list(
            (
                await session.scalars(
                    select(WithdrawalRequest)
                    .where(condition)
                    .order_by(WithdrawalRequest.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(WithdrawalRequest).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def get_user(
        session: AsyncSession, *, user_id: UUID, withdrawal_id: UUID
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest).where(
                WithdrawalRequest.id == withdrawal_id,
                WithdrawalRequest.user_id == user_id,
            )
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        return item

    @staticmethod
    async def cancel(
        session: AsyncSession, *, user_id: UUID, withdrawal_id: UUID
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.id == withdrawal_id,
                WithdrawalRequest.user_id == user_id,
            )
            .with_for_update(of=WithdrawalRequest)
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        if item.status == WithdrawalStatus.CANCELLED:
            return item
        if item.status != WithdrawalStatus.PENDING_REVIEW:
            raise AppError(
                "withdrawal_cannot_be_cancelled",
                "Эту заявку уже нельзя отменить",
                status_code=409,
            )
        await WalletService.apply_change(
            session,
            user_id=user_id,
            operation_type=WalletOperationType.WITHDRAWAL_REFUND,
            available_delta_atomic=item.total_debit_atomic,
            locked_delta_atomic=-item.total_debit_atomic,
            idempotency_key=f"withdrawal:cancel-refund:{item.id}",
            related_entity_type="withdrawal_request",
            related_entity_id=item.id,
            description="Возврат средств при отмене вывода пользователем",
        )
        item.status = WithdrawalStatus.CANCELLED
        item.rejected_at = utcnow()
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def list_admin(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[WithdrawalRequest], int]:
        items = list(
            (
                await session.scalars(
                    select(WithdrawalRequest)
                    .order_by(WithdrawalRequest.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(select(func.count()).select_from(WithdrawalRequest))
            or 0
        )
        return items, total

    @staticmethod
    async def get_admin(session: AsyncSession, withdrawal_id: UUID) -> WithdrawalRequest:
        item = await session.get(WithdrawalRequest, withdrawal_id)
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        return item

    @staticmethod
    async def update_amounts(
        session: AsyncSession,
        *,
        withdrawal_id: UUID,
        amount: str,
        fee: str,
        comment: str,
        expected_updated_at: datetime,
        idempotency_key: str,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> WithdrawalRequest:
        """Исправляет заявку вместе с балансом и неизменяемым журналом.

        Незавершённая заявка удерживает total_debit_atomic, в том числе старый
        излишек после уменьшения actual_fee. Для завершённой заявки этот
        излишек уже возвращён: её фактическое списание равно amount + fee.
        """
        try:
            item = await session.scalar(
                select(WithdrawalRequest)
                .where(WithdrawalRequest.id == withdrawal_id)
                .with_for_update(of=WithdrawalRequest)
                .execution_options(populate_existing=True)
            )
            if item is None:
                raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)

            amount_atomic = parse_amount(amount)
            fee_atomic = parse_amount(fee)
            total_atomic = amount_atomic + fee_atomic
            comment = comment.strip()
            if amount_atomic <= 0 or fee_atomic < 0:
                raise AppError("invalid_withdrawal_amounts", "Сумма должна быть положительной, комиссия — неотрицательной")
            if total_atomic > MAX_ATOMIC:
                raise AppError("withdrawal_amount_too_large", "Сумма вывода с комиссией превышает допустимый диапазон", status_code=409)
            if not 3 <= len(comment) <= 1000:
                raise AppError("invalid_adjustment_comment", "Укажите причину исправления: от 3 до 1000 символов")
            if not idempotency_key.strip() or len(idempotency_key) > 255:
                raise AppError("invalid_idempotency_key", "Некорректный Idempotency-Key")

            request_data = {
                "amount": format_amount(amount_atomic),
                "fee": format_amount(fee_atomic),
                "comment": comment,
                "expected_updated_at": ensure_utc(expected_updated_at).isoformat(),
                "admin_user_id": str(admin_user_id),
            }
            # Ограничиваем длину ключа для колонки VARCHAR(255) и отделяем
            # корректировки от остальных денежных операций.
            key_hash = sha256(idempotency_key.strip().encode("utf-8")).hexdigest()
            operation_key = f"withdrawal:amounts:{item.id}:{key_hash}"
            existing = await WalletService.find_transaction(session, operation_key)
            if existing is not None:
                if (
                    existing.operation_type != WalletOperationType.ADMIN_ADJUSTMENT
                    or existing.related_entity_type != "withdrawal_request"
                    or existing.related_entity_id != item.id
                    or existing.metadata_json.get("request") != request_data
                ):
                    raise AppError("idempotency_key_conflict", "Idempotency-Key уже использован для другого исправления", status_code=409)
                return item

            if item.status in {WithdrawalStatus.CANCELLED, WithdrawalStatus.REJECTED}:
                raise AppError(
                    "withdrawal_amounts_not_editable",
                    "Нельзя изменять суммы отменённой или отклонённой заявки: средства уже возвращены",
                    status_code=409,
                )
            if ensure_utc(item.updated_at) != ensure_utc(expected_updated_at):
                raise AppError(
                    "withdrawal_changed",
                    "Заявка уже изменена. Обновите страницу и проверьте суммы перед сохранением",
                    status_code=409,
                )

            old_data = {
                "amount": format_amount(item.amount_atomic),
                "fee": format_amount(item.fee_atomic),
                "held_total": format_amount(item.total_debit_atomic),
                "final_total": format_amount(item.amount_atomic + item.fee_atomic),
                "status": item.status.value,
                "admin_comment": item.admin_comment,
                "updated_at": ensure_utc(item.updated_at).isoformat(),
            }
            if item.status == WithdrawalStatus.COMPLETED:
                old_total = item.amount_atomic + item.fee_atomic
                available_delta = old_total - total_atomic
                locked_delta = 0
            else:
                old_total = item.total_debit_atomic
                available_delta = old_total - total_atomic
                locked_delta = -available_delta

            transaction, _ = await WalletService.apply_change(
                session,
                user_id=item.user_id,
                operation_type=WalletOperationType.ADMIN_ADJUSTMENT,
                available_delta_atomic=available_delta,
                locked_delta_atomic=locked_delta,
                idempotency_key=operation_key,
                related_entity_type="withdrawal_request",
                related_entity_id=item.id,
                description=f"Исправление суммы и комиссии вывода: {comment}",
                metadata_json={
                    "request": request_data,
                    "old_data": old_data,
                    "new_total": format_amount(total_atomic),
                },
            )
            item.amount_atomic = amount_atomic
            item.fee_atomic = fee_atomic
            item.total_debit_atomic = total_atomic
            item.admin_comment = comment
            # Версия меняется и при корректировке с нулевым денежным эффектом.
            item.updated_at = max(utcnow(), ensure_utc(item.updated_at) + timedelta(microseconds=1))
            await AuditService.record(
                session,
                admin_user_id=admin_user_id,
                action="withdrawal_amounts_updated",
                entity_type="withdrawal_request",
                entity_id=item.id,
                old_data=old_data,
                new_data={
                    "amount": format_amount(amount_atomic),
                    "fee": format_amount(fee_atomic),
                    "held_total": format_amount(total_atomic),
                    "final_total": format_amount(total_atomic),
                    "status": item.status.value,
                    "comment": comment,
                    "available_delta": format_amount(available_delta),
                    "locked_delta": format_amount(locked_delta),
                    "wallet_transaction_id": str(transaction.id),
                },
                ip_address=ip_address,
            )
            await session.commit()
            await session.refresh(item)
            return item
        except Exception:
            await session.rollback()
            raise

    @staticmethod
    async def approve(
        session: AsyncSession,
        *,
        withdrawal_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .with_for_update(of=WithdrawalRequest)
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        if item.status == WithdrawalStatus.APPROVED:
            return item
        if item.status != WithdrawalStatus.PENDING_REVIEW:
            raise AppError("invalid_withdrawal_status", "Заявка не ожидает подтверждения", status_code=409)
        old_status = item.status.value
        item.status = WithdrawalStatus.APPROVED
        item.approved_by_admin_id = admin_user_id
        item.approved_at = utcnow()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="withdrawal_approved",
            entity_type="withdrawal_request",
            entity_id=item.id,
            old_data={"status": old_status},
            new_data={"status": item.status.value},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def reject(
        session: AsyncSession,
        *,
        withdrawal_id: UUID,
        comment: str,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .with_for_update(of=WithdrawalRequest)
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        if item.status == WithdrawalStatus.REJECTED:
            return item
        if item.status not in {
            WithdrawalStatus.PENDING_REVIEW,
            WithdrawalStatus.APPROVED,
        }:
            raise AppError("invalid_withdrawal_status", "Эту заявку уже нельзя отклонить", status_code=409)
        old_status = item.status.value
        await WalletService.apply_change(
            session,
            user_id=item.user_id,
            operation_type=WalletOperationType.WITHDRAWAL_REFUND,
            available_delta_atomic=item.total_debit_atomic,
            locked_delta_atomic=-item.total_debit_atomic,
            idempotency_key=f"withdrawal:reject-refund:{item.id}",
            related_entity_type="withdrawal_request",
            related_entity_id=item.id,
            description="Возврат средств после отклонения вывода",
        )
        item.status = WithdrawalStatus.REJECTED
        item.admin_comment = comment
        item.rejected_at = utcnow()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="withdrawal_rejected",
            entity_type="withdrawal_request",
            entity_id=item.id,
            old_data={"status": old_status},
            new_data={"status": item.status.value, "comment": comment},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def mark_sent(
        session: AsyncSession,
        *,
        withdrawal_id: UUID,
        txid: str,
        actual_fee: str,
        comment: str | None,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .with_for_update(of=WithdrawalRequest)
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        if item.status == WithdrawalStatus.SENT:
            if item.txid == txid:
                return item
            raise AppError("withdrawal_already_sent", "Заявка уже отмечена отправленной", status_code=409)
        if item.status != WithdrawalStatus.APPROVED:
            raise AppError("invalid_withdrawal_status", "Сначала подтвердите заявку", status_code=409)
        existing_txid = await session.scalar(
            select(WithdrawalRequest.id).where(
                WithdrawalRequest.txid == txid,
                WithdrawalRequest.id != item.id,
            )
        )
        if existing_txid is not None:
            raise AppError("withdrawal_txid_exists", "Этот TxID уже использован", status_code=409)

        actual_fee_atomic = parse_amount(actual_fee)
        actual_total = item.amount_atomic + actual_fee_atomic
        if actual_total > item.total_debit_atomic:
            extra = actual_total - item.total_debit_atomic
            await WalletService.apply_change(
                session,
                user_id=item.user_id,
                operation_type=WalletOperationType.WITHDRAWAL_HOLD,
                available_delta_atomic=-extra,
                locked_delta_atomic=extra,
                idempotency_key=f"withdrawal:fee-adjustment:{item.id}",
                related_entity_type="withdrawal_request",
                related_entity_id=item.id,
                description="Дополнительная блокировка фактической комиссии вывода",
            )
            item.total_debit_atomic = actual_total

        item.fee_atomic = actual_fee_atomic
        item.txid = txid
        item.admin_comment = comment
        item.status = WithdrawalStatus.SENT
        item.sent_at = utcnow()
        try:
            await AuditService.record(
                session,
                admin_user_id=admin_user_id,
                action="withdrawal_marked_sent",
                entity_type="withdrawal_request",
                entity_id=item.id,
                new_data={
                    "status": item.status.value,
                    "txid": txid,
                    "actual_fee": format_amount(actual_fee_atomic),
                },
                ip_address=ip_address,
            )
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError("withdrawal_txid_exists", "Этот TxID уже использован", status_code=409) from exc
        await session.refresh(item)
        return item

    @staticmethod
    async def complete(
        session: AsyncSession,
        *,
        withdrawal_id: UUID,
        comment: str | None,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> WithdrawalRequest:
        item = await session.scalar(
            select(WithdrawalRequest)
            .where(WithdrawalRequest.id == withdrawal_id)
            .with_for_update(of=WithdrawalRequest)
        )
        if item is None:
            raise AppError("withdrawal_not_found", "Заявка на вывод не найдена", status_code=404)
        if item.status == WithdrawalStatus.COMPLETED:
            return item
        if item.status != WithdrawalStatus.SENT:
            raise AppError("invalid_withdrawal_status", "Заявка ещё не отмечена отправленной", status_code=409)

        final_total = item.amount_atomic + item.fee_atomic
        if final_total > item.total_debit_atomic:
            raise AppError("withdrawal_hold_inconsistent", "Заблокированной суммы недостаточно", status_code=409)
        refund_difference = item.total_debit_atomic - final_total
        transaction, _ = await WalletService.apply_change(
            session,
            user_id=item.user_id,
            operation_type=WalletOperationType.WITHDRAWAL_COMPLETE,
            available_delta_atomic=refund_difference,
            locked_delta_atomic=-item.total_debit_atomic,
            idempotency_key=f"withdrawal:complete:{item.id}",
            related_entity_type="withdrawal_request",
            related_entity_id=item.id,
            description="Завершение ручного вывода USDT ERC-20",
            metadata_json={
                "txid": item.txid,
                "final_debit": format_amount(final_total),
                "refunded_fee_difference": format_amount(refund_difference),
            },
        )
        item.status = WithdrawalStatus.COMPLETED
        item.completed_at = utcnow()
        if comment:
            item.admin_comment = comment
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="withdrawal_completed",
            entity_type="withdrawal_request",
            entity_id=item.id,
            new_data={
                "status": item.status.value,
                "txid": item.txid,
                "wallet_transaction_id": str(transaction.id),
            },
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item
