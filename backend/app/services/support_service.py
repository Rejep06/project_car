"""Обращения поддержки, автоматическая привязка TxID и безопасные вложения."""

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.db.enums import SupportTicketStatus, UnmatchedDepositStatus, UserRole
from app.db.models import (
    BlockchainDeposit,
    DepositInvoice,
    SupportAttachment,
    SupportMessage,
    SupportTicket,
    UnmatchedDeposit,
    User,
)
from app.services.audit_service import AuditService
from app.services.deposit_service import DepositService
from app.utils.datetime import utcnow
from app.utils.files import StoredFile, resolve_attachment_path, store_support_upload


class SupportService:
    @staticmethod
    async def _resolve_txid_links(
        session: AsyncSession,
        *,
        user_id: UUID,
        txid: str | None,
    ) -> tuple[UUID | None, UUID | None, bool]:
        if not txid:
            return None, None, False
        deposit, unmatched = await DepositService.find_by_txid(session, txid)
        conflict = False
        if deposit is not None and deposit.credited_at is not None:
            invoice = deposit.deposit_invoice
            if invoice is not None and invoice.user_id != user_id:
                conflict = True
        if unmatched is not None and unmatched.status == UnmatchedDepositStatus.ASSIGNED:
            if unmatched.assigned_user_id != user_id:
                conflict = True
        return (
            deposit.id if deposit is not None else None,
            unmatched.id if unmatched is not None else None,
            conflict,
        )

    @staticmethod
    async def create_ticket(
        session: AsyncSession,
        *,
        user: User,
        category: object,
        subject: str,
        message: str,
        txid: str | None,
        related_deposit_invoice_id: UUID | None,
    ) -> SupportTicket:
        if related_deposit_invoice_id is not None:
            invoice = await session.scalar(
                select(DepositInvoice).where(
                    DepositInvoice.id == related_deposit_invoice_id,
                    DepositInvoice.user_id == user.id,
                )
            )
            if invoice is None:
                raise AppError(
                    "deposit_invoice_not_found",
                    "Связанная заявка на пополнение не найдена",
                    status_code=404,
                )
        deposit_id, unmatched_id, conflict = await SupportService._resolve_txid_links(
            session, user_id=user.id, txid=txid
        )
        ticket = SupportTicket(
            user_id=user.id,
            category=category,
            subject=subject,
            status=SupportTicketStatus.OPEN,
            related_deposit_invoice_id=related_deposit_invoice_id,
            related_blockchain_deposit_id=deposit_id,
            related_unmatched_deposit_id=unmatched_id,
            txid_conflict=conflict,
        )
        session.add(ticket)
        await session.flush()
        first_message = SupportMessage(
            ticket_id=ticket.id,
            author_user_id=user.id,
            message=message,
            txid=txid,
            created_at=utcnow(),
        )
        session.add(first_message)
        await session.commit()
        return await SupportService.get_ticket_admin(session, ticket.id)

    @staticmethod
    def _ticket_query():
        return select(SupportTicket).options(
            joinedload(SupportTicket.user),
            joinedload(SupportTicket.related_deposit_invoice),
            joinedload(SupportTicket.related_blockchain_deposit),
            joinedload(SupportTicket.related_unmatched_deposit).joinedload(
                UnmatchedDeposit.blockchain_deposit
            ),
            selectinload(SupportTicket.messages).joinedload(SupportMessage.author),
            selectinload(SupportTicket.messages).selectinload(
                SupportMessage.attachments
            ),
        )

    @staticmethod
    async def list_user(
        session: AsyncSession,
        *,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[SupportTicket], int]:
        condition = SupportTicket.user_id == user_id
        items = list(
            (
                await session.scalars(
                    SupportService._ticket_query()
                    .where(condition)
                    .order_by(SupportTicket.updated_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).unique().all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(SupportTicket).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def get_ticket_user(
        session: AsyncSession, *, user_id: UUID, ticket_id: UUID
    ) -> SupportTicket:
        ticket = await session.scalar(
            SupportService._ticket_query().where(
                SupportTicket.id == ticket_id,
                SupportTicket.user_id == user_id,
            )
        )
        if ticket is None:
            raise AppError("support_ticket_not_found", "Обращение не найдено", status_code=404)
        return ticket

    @staticmethod
    async def list_admin(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[SupportTicket], int]:
        items = list(
            (
                await session.scalars(
                    SupportService._ticket_query()
                    .order_by(SupportTicket.updated_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).unique().all()
        )
        total = int(
            await session.scalar(select(func.count()).select_from(SupportTicket)) or 0
        )
        return items, total

    @staticmethod
    async def get_ticket_admin(session: AsyncSession, ticket_id: UUID) -> SupportTicket:
        ticket = await session.scalar(
            SupportService._ticket_query().where(SupportTicket.id == ticket_id)
        )
        if ticket is None:
            raise AppError("support_ticket_not_found", "Обращение не найдено", status_code=404)
        return ticket

    @staticmethod
    async def add_message(
        session: AsyncSession,
        *,
        ticket_id: UUID,
        author: User,
        message: str,
        txid: str | None,
        is_admin: bool,
    ) -> SupportMessage:
        ticket = await session.scalar(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .with_for_update(of=SupportTicket)
        )
        if ticket is None:
            raise AppError("support_ticket_not_found", "Обращение не найдено", status_code=404)
        if not is_admin and ticket.user_id != author.id:
            raise AppError("support_ticket_not_found", "Обращение не найдено", status_code=404)
        if ticket.status == SupportTicketStatus.CLOSED:
            raise AppError("support_ticket_closed", "Закрытое обращение нельзя дополнять", status_code=409)

        if txid:
            deposit_id, unmatched_id, conflict = await SupportService._resolve_txid_links(
                session, user_id=ticket.user_id, txid=txid
            )
            ticket.related_blockchain_deposit_id = (
                ticket.related_blockchain_deposit_id or deposit_id
            )
            ticket.related_unmatched_deposit_id = (
                ticket.related_unmatched_deposit_id or unmatched_id
            )
            ticket.txid_conflict = ticket.txid_conflict or conflict

        ticket.updated_at = utcnow()
        support_message = SupportMessage(
            ticket_id=ticket.id,
            author_user_id=author.id,
            message=message,
            txid=txid,
            created_at=utcnow(),
        )
        session.add(support_message)
        if is_admin and ticket.status == SupportTicketStatus.OPEN:
            ticket.status = SupportTicketStatus.IN_REVIEW
        elif not is_admin and ticket.status == SupportTicketStatus.WAITING_USER:
            ticket.status = SupportTicketStatus.IN_REVIEW
        await session.commit()

        loaded = await session.scalar(
            select(SupportMessage)
            .options(
                joinedload(SupportMessage.author),
                selectinload(SupportMessage.attachments),
            )
            .where(SupportMessage.id == support_message.id)
        )
        assert loaded is not None
        return loaded

    @staticmethod
    async def add_attachments(
        session: AsyncSession,
        *,
        message_id: UUID,
        requester: User,
        files: list[UploadFile],
        settings: Settings | None = None,
    ) -> list[SupportAttachment]:
        settings = settings or get_settings()
        message = await session.scalar(
            select(SupportMessage)
            .options(
                selectinload(SupportMessage.ticket),
                selectinload(SupportMessage.attachments),
            )
            .where(SupportMessage.id == message_id)
            .with_for_update(of=SupportMessage)
        )
        if message is None:
            raise AppError("support_message_not_found", "Сообщение не найдено", status_code=404)
        ticket = await session.scalar(
            select(SupportTicket)
            .where(SupportTicket.id == message.ticket_id)
            .with_for_update(of=SupportTicket)
        )
        assert ticket is not None
        is_admin = requester.role == UserRole.ADMIN
        if not is_admin and (
            ticket.user_id != requester.id
            or message.author_user_id != requester.id
        ):
            raise AppError(
                "support_message_not_found",
                "Сообщение не найдено",
                status_code=404,
            )
        if ticket.status == SupportTicketStatus.CLOSED:
            raise AppError(
                "support_ticket_closed",
                "К закрытому обращению нельзя прикреплять файлы",
                status_code=409,
            )
        if not files:
            raise AppError("attachments_required", "Не переданы файлы")
        if len(message.attachments) + len(files) > settings.support_max_files_per_message:
            raise AppError(
                "too_many_attachments",
                f"К одному сообщению можно прикрепить не более {settings.support_max_files_per_message} файлов",
                status_code=409,
            )

        stored: list[StoredFile] = []
        try:
            for upload in files:
                stored.append(
                    await store_support_upload(
                        upload,
                        upload_dir=settings.support_upload_dir,
                        max_size_bytes=settings.support_max_file_size_bytes,
                    )
                )
            attachments = [
                SupportAttachment(
                    message_id=message.id,
                    original_filename=item.original_filename,
                    stored_filename=item.stored_filename,
                    mime_type=item.mime_type,
                    size_bytes=item.size_bytes,
                    file_path=item.file_path,
                    created_at=utcnow(),
                )
                for item in stored
            ]
            session.add_all(attachments)
            ticket.updated_at = utcnow()
            await session.commit()
            for attachment in attachments:
                await session.refresh(attachment)
            return attachments
        except Exception:
            await session.rollback()
            for item in stored:
                path = Path(item.file_path)
                if path.exists():
                    await asyncio.to_thread(path.unlink)
            raise

    @staticmethod
    async def get_attachment(
        session: AsyncSession,
        *,
        attachment_id: UUID,
        requester: User,
        settings: Settings | None = None,
    ) -> tuple[SupportAttachment, Path]:
        settings = settings or get_settings()
        attachment = await session.scalar(
            select(SupportAttachment)
            .options(
                joinedload(SupportAttachment.message).joinedload(
                    SupportMessage.ticket
                )
            )
            .where(SupportAttachment.id == attachment_id)
        )
        if attachment is None:
            raise AppError("attachment_not_found", "Вложение не найдено", status_code=404)
        if (
            requester.role != UserRole.ADMIN
            and attachment.message.ticket.user_id != requester.id
        ):
            raise AppError("attachment_not_found", "Вложение не найдено", status_code=404)
        path = resolve_attachment_path(
            attachment.file_path, settings.support_upload_dir
        )
        return attachment, path

    @staticmethod
    async def update_status(
        session: AsyncSession,
        *,
        ticket_id: UUID,
        status: SupportTicketStatus,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> SupportTicket:
        ticket = await session.scalar(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .with_for_update(of=SupportTicket)
        )
        if ticket is None:
            raise AppError("support_ticket_not_found", "Обращение не найдено", status_code=404)
        old_status = ticket.status
        ticket.status = status
        ticket.closed_at = utcnow() if status == SupportTicketStatus.CLOSED else None
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="support_ticket_status_changed",
            entity_type="support_ticket",
            entity_id=ticket.id,
            old_data={"status": old_status.value},
            new_data={"status": status.value},
            ip_address=ip_address,
        )
        await session.commit()
        return await SupportService.get_ticket_admin(session, ticket.id)

    @staticmethod
    async def resolve_deposit(
        session: AsyncSession,
        *,
        ticket_id: UUID,
        invoice_id: UUID | None,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> SupportTicket:
        ticket = await SupportService.get_ticket_admin(session, ticket_id)
        if ticket.txid_conflict:
            raise AppError(
                "deposit_txid_conflict",
                "TxID уже зачислен другому пользователю; требуется отдельная проверка",
                status_code=409,
            )
        if ticket.related_unmatched_deposit_id is None:
            raise AppError(
                "unmatched_deposit_not_linked",
                "К обращению не привязан нераспознанный депозит",
                status_code=409,
            )
        await DepositService.assign_unmatched(
            session,
            unmatched_id=ticket.related_unmatched_deposit_id,
            user_id=ticket.user_id,
            invoice_id=invoice_id or ticket.related_deposit_invoice_id,
            admin_user_id=admin_user_id,
            ip_address=ip_address,
        )
        ticket = await session.scalar(
            select(SupportTicket)
            .where(SupportTicket.id == ticket_id)
            .with_for_update(of=SupportTicket)
        )
        assert ticket is not None
        old_status = ticket.status
        ticket.status = SupportTicketStatus.RESOLVED
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="support_deposit_resolved",
            entity_type="support_ticket",
            entity_id=ticket.id,
            old_data={"status": old_status.value},
            new_data={"status": ticket.status.value},
            ip_address=ip_address,
        )
        await session.commit()
        return await SupportService.get_ticket_admin(session, ticket.id)
