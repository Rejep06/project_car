"""Покупка билетов, розыгрыш, ручной выбор и выдача призов."""

from __future__ import annotations

import secrets
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.db.enums import (
    LotteryPrizeType,
    LotteryStatus,
    LotteryTicketStatus,
    LotteryWinnerSelectionMethod,
    LotteryWinnerStatus,
    NotificationType,
    WalletOperationType,
)
from app.db.models import (
    Lottery,
    LotteryPrize,
    LotteryTicket,
    LotteryTicketPurchase,
    LotteryWinner,
    User,
)
from app.schemas.lottery import (
    LotteryAdminRead,
    LotteryAdminTicketRead,
    LotteryCreate,
    LotteryDetailRead,
    LotteryPrizeCreate,
    LotteryPrizeRead,
    LotteryPrizeUpdate,
    LotteryPurchaseRead,
    LotterySummaryRead,
    LotteryTicketRead,
    LotteryUpdate,
    LotteryWinnerAdminRead,
    LotteryWinnerPublicRead,
)
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.services.wallet_service import WalletService
from app.utils.datetime import ensure_utc, utcnow
from app.utils.money import format_amount, parse_amount


class LotteryService:
    @staticmethod
    def _mask_email(email: str) -> str:
        local, _, domain = email.partition("@")
        if not domain:
            return "***"
        visible = local[:1] if local else "*"
        return f"{visible}***@{domain}"

    @staticmethod
    def _telegram_url(contact: str | None) -> str | None:
        if not contact:
            return None
        normalized = contact.strip()
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized
        username = normalized.lstrip("@").strip()
        return f"https://t.me/{username}" if username else None

    @staticmethod
    async def _ticket_count(
        session: AsyncSession, lottery_id: UUID, user_id: UUID | None = None
    ) -> int:
        conditions = [
            LotteryTicket.lottery_id == lottery_id,
            LotteryTicket.status == LotteryTicketStatus.ACTIVE,
        ]
        if user_id is not None:
            conditions.append(LotteryTicket.user_id == user_id)
        return int(
            await session.scalar(
                select(func.count()).select_from(LotteryTicket).where(*conditions)
            )
            or 0
        )

    @staticmethod
    async def _confirmed_winner_count(
        session: AsyncSession, lottery_id: UUID
    ) -> int:
        return int(
            await session.scalar(
                select(func.count())
                .select_from(LotteryWinner)
                .where(
                    LotteryWinner.lottery_id == lottery_id,
                    LotteryWinner.status == LotteryWinnerStatus.CONFIRMED,
                )
            )
            or 0
        )

    @staticmethod
    async def _load_lottery(
        session: AsyncSession, lottery_id: UUID, *, lock: bool = False
    ) -> Lottery:
        stmt = (
            select(Lottery)
            .options(selectinload(Lottery.prizes))
            .where(Lottery.id == lottery_id)
        )
        if lock:
            stmt = stmt.with_for_update(of=Lottery)
        item = await session.scalar(stmt)
        if item is None:
            raise AppError("lottery_not_found", "Лотерея не найдена", status_code=404)
        return item

    @staticmethod
    async def _public_winners(
        session: AsyncSession, lottery_id: UUID
    ) -> list[LotteryWinnerPublicRead]:
        winners = list(
            (
                await session.scalars(
                    select(LotteryWinner)
                    .options(
                        selectinload(LotteryWinner.prize),
                        selectinload(LotteryWinner.ticket),
                        selectinload(LotteryWinner.user),
                    )
                    .where(
                        LotteryWinner.lottery_id == lottery_id,
                        LotteryWinner.status == LotteryWinnerStatus.CONFIRMED,
                    )
                    .order_by(LotteryWinner.confirmed_at, LotteryWinner.selected_at)
                )
            ).all()
        )
        return [
            LotteryWinnerPublicRead(
                id=item.id,
                prize_id=item.prize_id,
                prize_title=item.prize.title,
                ticket_code=item.ticket.ticket_code,
                winner_email_masked=LotteryService._mask_email(item.user.email),
                confirmed_at=item.confirmed_at or item.selected_at,
            )
            for item in winners
        ]

    @classmethod
    async def _summary(
        cls, session: AsyncSession, lottery: Lottery
    ) -> LotterySummaryRead:
        return LotterySummaryRead.from_lottery(
            lottery,
            tickets_sold=await cls._ticket_count(session, lottery.id),
            confirmed_winners_count=await cls._confirmed_winner_count(
                session, lottery.id
            ),
        )

    @classmethod
    async def list_public(
        cls, session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[LotterySummaryRead], int]:
        condition = Lottery.status.in_(
            [
                LotteryStatus.PUBLISHED,
                LotteryStatus.AWAITING_CONFIRMATION,
                LotteryStatus.COMPLETED,
            ]
        )
        lotteries = list(
            (
                await session.scalars(
                    select(Lottery)
                    .where(condition)
                    .order_by(Lottery.sales_end_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(Lottery).where(condition)
            )
            or 0
        )
        return [await cls._summary(session, item) for item in lotteries], total

    @classmethod
    async def get_public(
        cls, session: AsyncSession, lottery_id: UUID
    ) -> LotteryDetailRead:
        lottery = await cls._load_lottery(session, lottery_id)
        if lottery.status == LotteryStatus.DRAFT:
            raise AppError("lottery_not_found", "Лотерея не найдена", status_code=404)
        summary = await cls._summary(session, lottery)
        return LotteryDetailRead(
            **summary.model_dump(),
            manager_telegram=lottery.manager_telegram,
            rules_text=lottery.rules_text,
            rules_version=lottery.rules_version,
            prizes=[LotteryPrizeRead.from_prize(item) for item in lottery.prizes],
            winners=await cls._public_winners(session, lottery.id),
        )

    @staticmethod
    def _ticket_read(ticket: LotteryTicket) -> LotteryTicketRead:
        # Неподтверждённый выбор остаётся внутренним решением администратора:
        # пользователь получает поздравление и сведения о призе только после
        # окончательного подтверждения.
        winner = (
            ticket.winner
            if ticket.winner is not None
            and ticket.winner.status == LotteryWinnerStatus.CONFIRMED
            else None
        )
        prize = winner.prize if winner is not None else None
        return LotteryTicketRead(
            id=ticket.id,
            lottery_id=ticket.lottery_id,
            lottery_title=ticket.lottery.title,
            ticket_code=ticket.ticket_code,
            price=format_amount(ticket.price_atomic),
            status=ticket.status,
            purchased_at=ticket.purchased_at,
            draw_at=ticket.lottery.draw_at,
            winner_status=winner.status if winner else None,
            prize_title=prize.title if prize else None,
            prize_type=prize.prize_type if prize else None,
            prize_amount=(
                format_amount(prize.amount_atomic)
                if prize and prize.amount_atomic is not None
                else None
            ),
            claim_contact=winner.claim_contact if winner else None,
        )

    @classmethod
    async def list_user_tickets(
        cls,
        session: AsyncSession,
        *,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[LotteryTicketRead], int]:
        condition = LotteryTicket.user_id == user_id
        tickets = list(
            (
                await session.scalars(
                    select(LotteryTicket)
                    .options(
                        selectinload(LotteryTicket.lottery),
                        selectinload(LotteryTicket.winner).selectinload(
                            LotteryWinner.prize
                        ),
                    )
                    .where(condition)
                    .order_by(LotteryTicket.purchased_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(LotteryTicket).where(condition)
            )
            or 0
        )
        return [cls._ticket_read(item) for item in tickets], total

    @classmethod
    async def list_user_lottery_tickets(
        cls, session: AsyncSession, *, user_id: UUID, lottery_id: UUID
    ) -> list[LotteryTicketRead]:
        tickets = list(
            (
                await session.scalars(
                    select(LotteryTicket)
                    .options(
                        selectinload(LotteryTicket.lottery),
                        selectinload(LotteryTicket.winner).selectinload(
                            LotteryWinner.prize
                        ),
                    )
                    .where(
                        LotteryTicket.user_id == user_id,
                        LotteryTicket.lottery_id == lottery_id,
                    )
                    .order_by(LotteryTicket.purchased_at, LotteryTicket.ticket_code)
                )
            ).all()
        )
        return [cls._ticket_read(item) for item in tickets]

    @staticmethod
    def _new_ticket_code(lottery_id: UUID) -> str:
        return f"{lottery_id.hex[:4].upper()}-{secrets.token_hex(8).upper()}"

    @classmethod
    async def purchase(
        cls,
        session: AsyncSession,
        *,
        user: User,
        lottery_id: UUID,
        quantity: int,
        idempotency_key: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> LotteryPurchaseRead:
        lottery = await cls._load_lottery(session, lottery_id, lock=True)
        locked_wallet = await WalletService.lock_wallet(session, user.id)
        existing_transaction = await WalletService.find_transaction(
            session, idempotency_key
        )
        if existing_transaction is not None:
            if (
                existing_transaction.wallet_id != locked_wallet.id
                or existing_transaction.operation_type
                != WalletOperationType.LOTTERY_TICKET_PURCHASE
                or existing_transaction.related_entity_type
                != "lottery_ticket_purchase"
                or existing_transaction.related_entity_id is None
            ):
                raise AppError(
                    "idempotency_key_conflict",
                    "Запрос уже использован для другой операции",
                    status_code=409,
                )
            purchase = await session.scalar(
                select(LotteryTicketPurchase)
                .options(
                    selectinload(LotteryTicketPurchase.tickets).selectinload(
                        LotteryTicket.lottery
                    ),
                    selectinload(LotteryTicketPurchase.tickets)
                    .selectinload(LotteryTicket.winner)
                    .selectinload(LotteryWinner.prize),
                )
                .where(
                    LotteryTicketPurchase.id
                    == existing_transaction.related_entity_id,
                    LotteryTicketPurchase.user_id == user.id,
                    LotteryTicketPurchase.lottery_id == lottery.id,
                )
            )
            if purchase is None:
                raise AppError(
                    "idempotency_key_conflict",
                    "Запрос уже использован для другой лотереи",
                    status_code=409,
                )
            if purchase.quantity != quantity:
                raise AppError(
                    "idempotency_key_conflict",
                    "Запрос уже использован для другого количества билетов",
                    status_code=409,
                )
            return LotteryPurchaseRead(
                purchase_id=purchase.id,
                lottery_id=purchase.lottery_id,
                quantity=purchase.quantity,
                total_amount=format_amount(purchase.total_amount_atomic),
                tickets=[cls._ticket_read(item) for item in purchase.tickets],
                created_at=purchase.created_at,
            )

        # Validate only a new purchase. A retry of a committed request must
        # remain recoverable after the sale closes or a ticket limit is met.
        if user.is_frozen:
            raise AppError(
                "user_frozen", "Операции пользователя временно недоступны", status_code=403
            )
        now = utcnow()
        sold = await cls._ticket_count(session, lottery.id)
        if lottery.status != LotteryStatus.PUBLISHED:
            raise AppError(
                "lottery_sales_closed", "Продажа билетов недоступна", status_code=409
            )
        if now < ensure_utc(lottery.sales_start_at):
            raise AppError(
                "lottery_sales_not_started",
                "Продажа билетов ещё не началась",
                status_code=409,
            )
        if now >= ensure_utc(lottery.sales_end_at):
            raise AppError(
                "lottery_sales_closed", "Срок покупки билетов завершён", status_code=409
            )
        if lottery.max_tickets_total is not None and sold + quantity > lottery.max_tickets_total:
            raise AppError(
                "lottery_ticket_limit",
                "В лотерее осталось меньше билетов, чем указано в запросе",
                status_code=409,
            )
        user_count = await cls._ticket_count(session, lottery.id, user.id)
        if user_count + quantity > lottery.max_tickets_per_user:
            raise AppError(
                "lottery_user_ticket_limit",
                f"На одного пользователя доступно не более {lottery.max_tickets_per_user} билетов",
                status_code=409,
            )

        purchase_id = uuid4()
        total_atomic = lottery.ticket_price_atomic * quantity
        transaction, _ = await WalletService.apply_change(
            session,
            user_id=user.id,
            operation_type=WalletOperationType.LOTTERY_TICKET_PURCHASE,
            available_delta_atomic=-total_atomic,
            locked_delta_atomic=0,
            idempotency_key=idempotency_key,
            related_entity_type="lottery_ticket_purchase",
            related_entity_id=purchase_id,
            description=f"Покупка билетов: {lottery.title}",
            metadata_json={
                "lottery_id": str(lottery.id),
                "quantity": quantity,
                "rules_version": lottery.rules_version,
            },
            locked_wallet=locked_wallet,
        )
        purchase = LotteryTicketPurchase(
            id=purchase_id,
            lottery_id=lottery.id,
            user_id=user.id,
            quantity=quantity,
            total_amount_atomic=total_atomic,
            wallet_transaction_id=transaction.id,
            rules_version=lottery.rules_version,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:500] or None,
        )
        session.add(purchase)
        tickets: list[LotteryTicket] = []
        used_codes: set[str] = set()
        for _ in range(quantity):
            code = cls._new_ticket_code(lottery.id)
            while code in used_codes:
                code = cls._new_ticket_code(lottery.id)
            used_codes.add(code)
            ticket = LotteryTicket(
                purchase_id=purchase.id,
                lottery_id=lottery.id,
                user_id=user.id,
                ticket_code=code,
                price_atomic=lottery.ticket_price_atomic,
                status=LotteryTicketStatus.ACTIVE,
                purchased_at=now,
            )
            session.add(ticket)
            tickets.append(ticket)
        await session.commit()

        for ticket in tickets:
            await session.refresh(ticket)
            ticket.lottery = lottery
            ticket.winner = None
        return LotteryPurchaseRead(
            purchase_id=purchase.id,
            lottery_id=lottery.id,
            quantity=quantity,
            total_amount=format_amount(total_atomic),
            tickets=[cls._ticket_read(item) for item in tickets],
            created_at=purchase.created_at,
        )

    @classmethod
    async def list_admin(
        cls, session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[LotterySummaryRead], int]:
        lotteries = list(
            (
                await session.scalars(
                    select(Lottery)
                    .order_by(Lottery.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(await session.scalar(select(func.count()).select_from(Lottery)) or 0)
        return [await cls._summary(session, item) for item in lotteries], total

    @classmethod
    async def _admin_winners(
        cls, session: AsyncSession, lottery_id: UUID
    ) -> list[LotteryWinnerAdminRead]:
        winners = list(
            (
                await session.scalars(
                    select(LotteryWinner)
                    .options(
                        selectinload(LotteryWinner.prize),
                        selectinload(LotteryWinner.ticket),
                        selectinload(LotteryWinner.user),
                    )
                    .where(
                        LotteryWinner.lottery_id == lottery_id,
                        LotteryWinner.status != LotteryWinnerStatus.CANCELLED,
                    )
                    .order_by(LotteryWinner.selected_at)
                )
            ).all()
        )
        return [
            LotteryWinnerAdminRead(
                id=item.id,
                lottery_id=item.lottery_id,
                prize_id=item.prize_id,
                prize_title=item.prize.title,
                prize_type=item.prize.prize_type,
                prize_amount=(
                    format_amount(item.prize.amount_atomic)
                    if item.prize.amount_atomic is not None
                    else None
                ),
                ticket_id=item.ticket_id,
                ticket_code=item.ticket.ticket_code,
                user_id=item.user_id,
                user_email=item.user.email,
                selection_method=item.selection_method,
                status=item.status,
                selected_at=item.selected_at,
                confirmed_at=item.confirmed_at,
                claim_contact=item.claim_contact,
                confirmation_note=item.confirmation_note,
            )
            for item in winners
        ]

    @classmethod
    async def get_admin(
        cls, session: AsyncSession, lottery_id: UUID
    ) -> LotteryAdminRead:
        lottery = await cls._load_lottery(session, lottery_id)
        summary = await cls._summary(session, lottery)
        winners = await cls._admin_winners(session, lottery.id)
        public_winners = await cls._public_winners(session, lottery.id)
        return LotteryAdminRead(
            **summary.model_dump(),
            manager_telegram=lottery.manager_telegram,
            rules_text=lottery.rules_text,
            rules_version=lottery.rules_version,
            prizes=[LotteryPrizeRead.from_prize(item) for item in lottery.prizes],
            winners=public_winners,
            created_by_user_id=lottery.created_by_user_id,
            published_at=lottery.published_at,
            completed_at=lottery.completed_at,
            pending_winners_count=sum(
                1 for item in winners if item.status == LotteryWinnerStatus.PENDING
            ),
            admin_winners=winners,
        )

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        data: LotteryCreate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> Lottery:
        item = Lottery(
            title=data.title.strip(),
            description=data.description.strip(),
            cover_image_url=data.cover_image_url,
            ticket_price_atomic=parse_amount(data.ticket_price),
            sales_start_at=ensure_utc(data.sales_start_at),
            sales_end_at=ensure_utc(data.sales_end_at),
            draw_at=ensure_utc(data.draw_at),
            max_tickets_total=data.max_tickets_total,
            max_tickets_per_user=data.max_tickets_per_user,
            manager_telegram=data.manager_telegram,
            rules_text=data.rules_text.strip(),
            rules_version=data.rules_version.strip(),
            created_by_user_id=admin_user_id,
            status=LotteryStatus.DRAFT,
        )
        session.add(item)
        await session.flush()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_created",
            entity_type="lottery",
            entity_id=item.id,
            new_data={"title": item.title},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        data: LotteryUpdate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> Lottery:
        item = await cls._load_lottery(session, lottery_id, lock=True)
        if item.status in {LotteryStatus.COMPLETED, LotteryStatus.CANCELLED}:
            raise AppError(
                "lottery_locked", "Завершённую лотерею нельзя изменять", status_code=409
            )
        changes = data.model_dump(exclude_unset=True)
        sold = await cls._ticket_count(session, item.id)

        merged = {
            "title": item.title,
            "description": item.description,
            "cover_image_url": item.cover_image_url,
            "ticket_price": format_amount(item.ticket_price_atomic),
            "sales_start_at": item.sales_start_at,
            "sales_end_at": item.sales_end_at,
            "draw_at": item.draw_at,
            "max_tickets_total": item.max_tickets_total,
            "max_tickets_per_user": item.max_tickets_per_user,
            "manager_telegram": item.manager_telegram,
            "rules_text": item.rules_text,
            "rules_version": item.rules_version,
            **changes,
        }
        validated = LotteryCreate.model_validate(merged)
        if sold:
            protected_changed = any(
                (
                    parse_amount(validated.ticket_price) != item.ticket_price_atomic,
                    ensure_utc(validated.sales_start_at) != ensure_utc(item.sales_start_at),
                    ensure_utc(validated.sales_end_at) != ensure_utc(item.sales_end_at),
                    ensure_utc(validated.draw_at) != ensure_utc(item.draw_at),
                    validated.max_tickets_total != item.max_tickets_total,
                    validated.max_tickets_per_user != item.max_tickets_per_user,
                    validated.rules_text.strip() != item.rules_text,
                    validated.rules_version.strip() != item.rules_version,
                )
            )
            if protected_changed:
                raise AppError(
                    "lottery_has_tickets",
                    "После первой покупки нельзя менять цену, даты, лимиты и правила",
                    status_code=409,
                )

        old_data = {"title": item.title, "status": item.status.value}
        item.title = validated.title.strip()
        item.description = validated.description.strip()
        item.cover_image_url = validated.cover_image_url
        item.ticket_price_atomic = parse_amount(validated.ticket_price)
        item.sales_start_at = ensure_utc(validated.sales_start_at)
        item.sales_end_at = ensure_utc(validated.sales_end_at)
        item.draw_at = ensure_utc(validated.draw_at)
        item.max_tickets_total = validated.max_tickets_total
        item.max_tickets_per_user = validated.max_tickets_per_user
        item.manager_telegram = validated.manager_telegram
        item.rules_text = validated.rules_text.strip()
        item.rules_version = validated.rules_version.strip()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_updated",
            entity_type="lottery",
            entity_id=item.id,
            old_data=old_data,
            new_data={"title": item.title, "status": item.status.value},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def publish(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> Lottery:
        item = await cls._load_lottery(session, lottery_id, lock=True)
        if item.status == LotteryStatus.PUBLISHED:
            return item
        if item.status != LotteryStatus.DRAFT:
            raise AppError(
                "invalid_lottery_status",
                "Эту лотерею нельзя опубликовать",
                status_code=409,
            )
        if not item.prizes:
            raise AppError(
                "lottery_prizes_required",
                "Добавьте хотя бы один приз",
                status_code=409,
            )
        for prize in item.prizes:
            if (
                prize.prize_type == LotteryPrizeType.PHYSICAL
                and not (prize.manager_telegram or item.manager_telegram)
            ):
                raise AppError(
                    "lottery_manager_contact_required",
                    "Для неденежного приза укажите Telegram менеджера",
                    status_code=409,
                )
        if ensure_utc(item.sales_end_at) <= utcnow():
            raise AppError(
                "lottery_deadline_passed",
                "Нельзя опубликовать лотерею с прошедшим дедлайном",
                status_code=409,
            )
        item.status = LotteryStatus.PUBLISHED
        item.published_at = utcnow()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_published",
            entity_type="lottery",
            entity_id=item.id,
            new_data={"title": item.title},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def create_prize(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        data: LotteryPrizeCreate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> LotteryPrize:
        lottery = await cls._load_lottery(session, lottery_id, lock=True)
        if await cls._ticket_count(session, lottery.id):
            raise AppError(
                "lottery_has_tickets",
                "После первой покупки состав призов нельзя менять",
                status_code=409,
            )
        item = LotteryPrize(
            lottery_id=lottery.id,
            title=data.title.strip(),
            description=data.description.strip(),
            prize_type=data.prize_type,
            amount_atomic=parse_amount(data.amount) if data.amount else None,
            quantity=data.quantity,
            sort_order=data.sort_order,
            image_url=data.image_url,
            manager_telegram=data.manager_telegram,
        )
        session.add(item)
        await session.flush()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_prize_created",
            entity_type="lottery_prize",
            entity_id=item.id,
            new_data={"lottery_id": str(lottery.id), "title": item.title},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def update_prize(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        prize_id: UUID,
        data: LotteryPrizeUpdate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> LotteryPrize:
        item = await session.scalar(
            select(LotteryPrize)
            .where(
                LotteryPrize.id == prize_id,
                LotteryPrize.lottery_id == lottery_id,
            )
            .with_for_update(of=LotteryPrize)
        )
        if item is None:
            raise AppError("lottery_prize_not_found", "Приз не найден", status_code=404)
        if await cls._ticket_count(session, item.lottery_id):
            raise AppError(
                "lottery_has_tickets",
                "После первой покупки состав призов нельзя менять",
                status_code=409,
            )
        merged = {
            "title": item.title,
            "description": item.description,
            "prize_type": item.prize_type,
            "amount": (
                format_amount(item.amount_atomic)
                if item.amount_atomic is not None
                else None
            ),
            "quantity": item.quantity,
            "sort_order": item.sort_order,
            "image_url": item.image_url,
            "manager_telegram": item.manager_telegram,
            **data.model_dump(exclude_unset=True),
        }
        validated = LotteryPrizeCreate.model_validate(merged)
        item.title = validated.title.strip()
        item.description = validated.description.strip()
        item.prize_type = validated.prize_type
        item.amount_atomic = parse_amount(validated.amount) if validated.amount else None
        item.quantity = validated.quantity
        item.sort_order = validated.sort_order
        item.image_url = validated.image_url
        item.manager_telegram = validated.manager_telegram
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_prize_updated",
            entity_type="lottery_prize",
            entity_id=item.id,
            new_data={"title": item.title},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def delete_prize(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        prize_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> None:
        item = await session.scalar(
            select(LotteryPrize)
            .where(
                LotteryPrize.id == prize_id,
                LotteryPrize.lottery_id == lottery_id,
            )
            .with_for_update(of=LotteryPrize)
        )
        if item is None:
            return
        if await cls._ticket_count(session, item.lottery_id):
            raise AppError(
                "lottery_has_tickets",
                "После первой покупки состав призов нельзя менять",
                status_code=409,
            )
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_prize_deleted",
            entity_type="lottery_prize",
            entity_id=item.id,
            old_data={"title": item.title, "lottery_id": str(item.lottery_id)},
            ip_address=ip_address,
        )
        await session.delete(item)
        await session.commit()

    @classmethod
    async def list_admin_tickets(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        offset: int,
        limit: int,
        search: str | None = None,
    ) -> tuple[list[LotteryAdminTicketRead], int]:
        await cls._load_lottery(session, lottery_id)
        conditions = [LotteryTicket.lottery_id == lottery_id]
        normalized_search = (search or "").strip()
        if normalized_search:
            conditions.append(
                or_(
                    LotteryTicket.ticket_code.contains(
                        normalized_search, autoescape=True
                    ),
                    User.email.contains(normalized_search.lower(), autoescape=True),
                )
            )

        base = (
            select(LotteryTicket)
            .join(User, User.id == LotteryTicket.user_id)
            .where(*conditions)
        )
        tickets = list(
            (
                await session.scalars(
                    base.options(
                        selectinload(LotteryTicket.user),
                        selectinload(LotteryTicket.winner),
                    )
                    .order_by(LotteryTicket.purchased_at, LotteryTicket.ticket_code)
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count())
                .select_from(LotteryTicket)
                .join(User, User.id == LotteryTicket.user_id)
                .where(*conditions)
            )
            or 0
        )
        return [
            LotteryAdminTicketRead(
                id=item.id,
                user_id=item.user_id,
                user_email=item.user.email,
                ticket_code=item.ticket_code,
                status=item.status,
                purchased_at=item.purchased_at,
                is_winner=item.winner is not None
                and item.winner.status != LotteryWinnerStatus.CANCELLED,
            )
            for item in tickets
        ], total

    @staticmethod
    def _validate_draw_time(lottery: Lottery) -> None:
        if lottery.status in {LotteryStatus.COMPLETED, LotteryStatus.CANCELLED}:
            raise AppError(
                "invalid_lottery_status", "Розыгрыш уже завершён", status_code=409
            )
        if ensure_utc(lottery.draw_at) > utcnow():
            raise AppError(
                "lottery_draw_not_ready",
                "Дата результатов ещё не наступила",
                status_code=409,
            )

    @classmethod
    async def draw_random(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> list[LotteryWinnerAdminRead]:
        lottery = await cls._load_lottery(session, lottery_id, lock=True)
        cls._validate_draw_time(lottery)
        tickets = list(
            (
                await session.scalars(
                    select(LotteryTicket)
                    .where(
                        LotteryTicket.lottery_id == lottery.id,
                        LotteryTicket.status == LotteryTicketStatus.ACTIVE,
                    )
                    .order_by(LotteryTicket.id)
                    .with_for_update(of=LotteryTicket)
                )
            ).all()
        )
        if not tickets:
            raise AppError(
                "lottery_has_no_tickets", "В лотерее нет билетов", status_code=409
            )
        current = list(
            (
                await session.scalars(
                    select(LotteryWinner)
                    .where(
                        LotteryWinner.lottery_id == lottery.id,
                        LotteryWinner.status != LotteryWinnerStatus.CANCELLED,
                    )
                    .with_for_update(of=LotteryWinner)
                )
            ).all()
        )
        used_ticket_ids = {item.ticket_id for item in current}
        available = [item for item in tickets if item.id not in used_ticket_ids]
        randomizer = secrets.SystemRandom()
        created = 0
        for prize in lottery.prizes:
            filled = sum(1 for item in current if item.prize_id == prize.id)
            slots = max(0, prize.quantity - filled)
            if slots == 0 or not available:
                continue
            chosen = randomizer.sample(available, min(slots, len(available)))
            chosen_ids = {item.id for item in chosen}
            available = [item for item in available if item.id not in chosen_ids]
            for ticket in chosen:
                winner = LotteryWinner(
                    lottery_id=lottery.id,
                    prize_id=prize.id,
                    ticket_id=ticket.id,
                    user_id=ticket.user_id,
                    selection_method=LotteryWinnerSelectionMethod.RANDOM,
                    status=LotteryWinnerStatus.PENDING,
                    selected_by_user_id=admin_user_id,
                )
                session.add(winner)
                created += 1
        if created == 0:
            raise AppError(
                "lottery_winners_already_selected",
                "Свободных призовых мест или билетов больше нет",
                status_code=409,
            )
        lottery.status = LotteryStatus.AWAITING_CONFIRMATION
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_random_draw",
            entity_type="lottery",
            entity_id=lottery.id,
            new_data={"selected_winners": created},
            ip_address=ip_address,
        )
        await session.commit()
        return await cls._admin_winners(session, lottery.id)

    @classmethod
    async def select_manual_winner(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        prize_id: UUID,
        ticket_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> LotteryWinnerAdminRead:
        lottery = await cls._load_lottery(session, lottery_id, lock=True)
        cls._validate_draw_time(lottery)
        prize = await session.scalar(
            select(LotteryPrize)
            .where(
                LotteryPrize.id == prize_id,
                LotteryPrize.lottery_id == lottery.id,
            )
            .with_for_update(of=LotteryPrize)
        )
        ticket = await session.scalar(
            select(LotteryTicket)
            .where(
                LotteryTicket.id == ticket_id,
                LotteryTicket.lottery_id == lottery.id,
                LotteryTicket.status == LotteryTicketStatus.ACTIVE,
            )
            .with_for_update(of=LotteryTicket)
        )
        if prize is None:
            raise AppError("lottery_prize_not_found", "Приз не найден", status_code=404)
        if ticket is None:
            raise AppError("lottery_ticket_not_found", "Билет не найден", status_code=404)
        existing_ticket = await session.scalar(
            select(LotteryWinner.id).where(
                LotteryWinner.ticket_id == ticket.id,
                LotteryWinner.status != LotteryWinnerStatus.CANCELLED,
            )
        )
        if existing_ticket is not None:
            raise AppError(
                "lottery_ticket_already_won",
                "Этот билет уже выбран победителем",
                status_code=409,
            )
        filled = int(
            await session.scalar(
                select(func.count())
                .select_from(LotteryWinner)
                .where(
                    LotteryWinner.prize_id == prize.id,
                    LotteryWinner.status != LotteryWinnerStatus.CANCELLED,
                )
            )
            or 0
        )
        if filled >= prize.quantity:
            raise AppError(
                "lottery_prize_slots_filled",
                "Все победители для этого приза уже выбраны",
                status_code=409,
            )
        winner = LotteryWinner(
            lottery_id=lottery.id,
            prize_id=prize.id,
            ticket_id=ticket.id,
            user_id=ticket.user_id,
            selection_method=LotteryWinnerSelectionMethod.MANUAL,
            status=LotteryWinnerStatus.PENDING,
            selected_by_user_id=admin_user_id,
        )
        session.add(winner)
        lottery.status = LotteryStatus.AWAITING_CONFIRMATION
        await session.flush()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_manual_winner_selected",
            entity_type="lottery_winner",
            entity_id=winner.id,
            new_data={
                "lottery_id": str(lottery.id),
                "ticket_id": str(ticket.id),
                "prize_id": str(prize.id),
            },
            ip_address=ip_address,
        )
        await session.commit()
        winners = await cls._admin_winners(session, lottery.id)
        return next(item for item in winners if item.id == winner.id)

    @classmethod
    async def remove_pending_winner(
        cls,
        session: AsyncSession,
        *,
        winner_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> None:
        winner = await session.scalar(
            select(LotteryWinner)
            .where(LotteryWinner.id == winner_id)
            .with_for_update(of=LotteryWinner)
        )
        if winner is None:
            return
        if winner.status != LotteryWinnerStatus.PENDING:
            raise AppError(
                "lottery_winner_already_confirmed",
                "Подтверждённого победителя нельзя удалить",
                status_code=409,
            )
        winner_id_value = winner.id
        lottery_id_value = winner.lottery_id
        ticket_id_value = winner.ticket_id
        prize_id_value = winner.prize_id
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_pending_winner_removed",
            entity_type="lottery_winner",
            entity_id=winner_id_value,
            old_data={
                "lottery_id": str(lottery_id_value),
                "ticket_id": str(ticket_id_value),
                "prize_id": str(prize_id_value),
                "status": LotteryWinnerStatus.PENDING.value,
            },
            ip_address=ip_address,
        )
        # Удаляем только неподтверждённый выбор. Так тот же билет можно выбрать
        # повторно, а уникальное ограничение ticket_id не блокирует новый выбор.
        await session.delete(winner)
        await session.commit()

    @classmethod
    async def _maybe_complete(
        cls, session: AsyncSession, lottery: Lottery
    ) -> None:
        ticket_count = await cls._ticket_count(session, lottery.id)
        total_slots = sum(prize.quantity for prize in lottery.prizes)
        target = min(ticket_count, total_slots)
        if target <= 0:
            return
        active_winners = int(
            await session.scalar(
                select(func.count())
                .select_from(LotteryWinner)
                .where(
                    LotteryWinner.lottery_id == lottery.id,
                    LotteryWinner.status != LotteryWinnerStatus.CANCELLED,
                )
            )
            or 0
        )
        pending = int(
            await session.scalar(
                select(func.count())
                .select_from(LotteryWinner)
                .where(
                    LotteryWinner.lottery_id == lottery.id,
                    LotteryWinner.status == LotteryWinnerStatus.PENDING,
                )
            )
            or 0
        )
        if active_winners >= target and pending == 0:
            lottery.status = LotteryStatus.COMPLETED
            lottery.completed_at = utcnow()

    @classmethod
    async def confirm_winner(
        cls,
        session: AsyncSession,
        *,
        winner_id: UUID,
        note: str | None,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> LotteryWinnerAdminRead:
        winner = await session.scalar(
            select(LotteryWinner)
            .options(
                selectinload(LotteryWinner.lottery).selectinload(Lottery.prizes),
                selectinload(LotteryWinner.prize),
                selectinload(LotteryWinner.ticket),
                selectinload(LotteryWinner.user),
            )
            .where(LotteryWinner.id == winner_id)
            .with_for_update(of=LotteryWinner)
        )
        if winner is None:
            raise AppError(
                "lottery_winner_not_found", "Победитель не найден", status_code=404
            )
        if winner.status == LotteryWinnerStatus.CONFIRMED:
            winners = await cls._admin_winners(session, winner.lottery_id)
            return next(item for item in winners if item.id == winner.id)
        if winner.status != LotteryWinnerStatus.PENDING:
            raise AppError(
                "invalid_lottery_winner_status",
                "Этого победителя нельзя подтвердить",
                status_code=409,
            )

        # Победителей могут подтверждать параллельно. Блокировка самой лотереи
        # гарантирует корректный переход в completed после последнего приза.
        lottery = await cls._load_lottery(
            session, winner.lottery_id, lock=True
        )
        prize = winner.prize
        contact = prize.manager_telegram or lottery.manager_telegram
        transaction_id: UUID | None = None
        if prize.prize_type == LotteryPrizeType.BALANCE:
            assert prize.amount_atomic is not None
            transaction, _ = await WalletService.apply_change(
                session,
                user_id=winner.user_id,
                operation_type=WalletOperationType.LOTTERY_PRIZE_CREDIT,
                available_delta_atomic=prize.amount_atomic,
                locked_delta_atomic=0,
                idempotency_key=f"lottery:winner:{winner.id}",
                related_entity_type="lottery_winner",
                related_entity_id=winner.id,
                description=f"Приз лотереи: {prize.title}",
                metadata_json={
                    "lottery_id": str(winner.lottery_id),
                    "prize_id": str(prize.id),
                    "ticket_id": str(winner.ticket_id),
                },
            )
            transaction_id = transaction.id
            notification_message = (
                f"На ваш баланс зачислено {format_amount(prize.amount_atomic)} USDT. "
                f"Победил билет {winner.ticket.ticket_code}."
            )
            action_url = "/account/wallet"
            contact = None
        else:
            if not contact:
                raise AppError(
                    "lottery_manager_contact_required",
                    "Укажите Telegram менеджера перед подтверждением приза",
                    status_code=409,
                )
            notification_message = (
                f"Вы выиграли «{prize.title}». Победил билет "
                f"{winner.ticket.ticket_code}. Свяжитесь с менеджером для получения приза: {contact}."
            )
            action_url = cls._telegram_url(contact)

        winner.status = LotteryWinnerStatus.CONFIRMED
        winner.confirmed_by_user_id = admin_user_id
        winner.confirmed_at = utcnow()
        winner.wallet_transaction_id = transaction_id
        winner.claim_contact = contact
        winner.confirmation_note = note
        await NotificationService.create(
            session,
            user_id=winner.user_id,
            notification_type=NotificationType.LOTTERY_WIN,
            title=f"Поздравляем! Вы выиграли в «{lottery.title}»",
            message=notification_message,
            action_url=action_url,
        )
        await EmailService.queue_lottery_win_email(
            session,
            recipient_email=winner.user.email,
            lottery_title=lottery.title,
            prize_title=prize.title,
            message=notification_message,
            manager_contact=contact,
        )
        await cls._maybe_complete(session, lottery)
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="lottery_winner_confirmed",
            entity_type="lottery_winner",
            entity_id=winner.id,
            new_data={
                "lottery_id": str(winner.lottery_id),
                "prize_id": str(prize.id),
                "user_id": str(winner.user_id),
                "wallet_transaction_id": (
                    str(transaction_id) if transaction_id else None
                ),
            },
            ip_address=ip_address,
        )
        await session.commit()
        winners = await cls._admin_winners(session, winner.lottery_id)
        return next(item for item in winners if item.id == winner.id)

    @classmethod
    async def confirm_all_winners(
        cls,
        session: AsyncSession,
        *,
        lottery_id: UUID,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> list[LotteryWinnerAdminRead]:
        ids = list(
            (
                await session.scalars(
                    select(LotteryWinner.id)
                    .where(
                        LotteryWinner.lottery_id == lottery_id,
                        LotteryWinner.status == LotteryWinnerStatus.PENDING,
                    )
                    .order_by(LotteryWinner.selected_at)
                )
            ).all()
        )
        if not ids:
            raise AppError(
                "lottery_no_pending_winners",
                "Нет победителей, ожидающих подтверждения",
                status_code=409,
            )
        for winner_id in ids:
            await cls.confirm_winner(
                session,
                winner_id=winner_id,
                note=None,
                admin_user_id=admin_user_id,
                ip_address=ip_address,
            )
        return await cls._admin_winners(session, lottery_id)
