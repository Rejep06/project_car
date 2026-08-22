"""Лотереи, призы, покупки билетов и подтверждённые победители."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    LotteryPrizeType,
    LotteryStatus,
    LotteryTicketStatus,
    LotteryWinnerSelectionMethod,
    LotteryWinnerStatus,
)
from app.utils.datetime import utcnow


class Lottery(TimestampMixin, Base):
    __tablename__ = "lotteries"
    __table_args__ = (
        CheckConstraint("ticket_price_atomic > 0", name="ticket_price_positive"),
        CheckConstraint(
            "max_tickets_total IS NULL OR max_tickets_total > 0",
            name="max_tickets_total_positive",
        ),
        CheckConstraint(
            "max_tickets_per_user > 0", name="max_tickets_per_user_positive"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[LotteryStatus] = mapped_column(
        Enum(
            LotteryStatus,
            name="lottery_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=LotteryStatus.DRAFT,
        index=True,
        nullable=False,
    )
    ticket_price_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sales_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    sales_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    draw_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    max_tickets_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_tickets_per_user: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    manager_telegram: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rules_text: Mapped[str] = mapped_column(Text, nullable=False)
    rules_version: Mapped[str] = mapped_column(String(40), default="1.0", nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by = relationship("User", lazy="selectin")
    prizes = relationship(
        "LotteryPrize",
        back_populates="lottery",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="LotteryPrize.sort_order, LotteryPrize.created_at",
    )
    tickets = relationship("LotteryTicket", back_populates="lottery", lazy="raise")
    winners = relationship("LotteryWinner", back_populates="lottery", lazy="raise")


class LotteryPrize(TimestampMixin, Base):
    __tablename__ = "lottery_prizes"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "amount_atomic IS NULL OR amount_atomic > 0", name="amount_positive"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lottery_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lotteries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    prize_type: Mapped[LotteryPrizeType] = mapped_column(
        Enum(
            LotteryPrizeType,
            name="lottery_prize_type",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    amount_atomic: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    manager_telegram: Mapped[str | None] = mapped_column(String(120), nullable=True)

    lottery = relationship("Lottery", back_populates="prizes", lazy="selectin")
    winners = relationship("LotteryWinner", back_populates="prize", lazy="raise")


class LotteryTicketPurchase(Base):
    __tablename__ = "lottery_ticket_purchases"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lottery_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lotteries.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    wallet_transaction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("wallet_transactions.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    rules_version: Mapped[str] = mapped_column(String(40), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=False
    )

    lottery = relationship("Lottery", lazy="selectin")
    user = relationship("User", lazy="selectin")
    wallet_transaction = relationship("WalletTransaction", lazy="selectin")
    tickets = relationship(
        "LotteryTicket",
        back_populates="purchase",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LotteryTicket(Base):
    __tablename__ = "lottery_tickets"
    __table_args__ = (
        UniqueConstraint("lottery_id", "ticket_code", name="uq_lottery_ticket_code"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    purchase_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lottery_ticket_purchases.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    lottery_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lotteries.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    ticket_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    price_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[LotteryTicketStatus] = mapped_column(
        Enum(
            LotteryTicketStatus,
            name="lottery_ticket_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=LotteryTicketStatus.ACTIVE,
        index=True,
        nullable=False,
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), index=True, nullable=False
    )

    purchase = relationship("LotteryTicketPurchase", back_populates="tickets", lazy="selectin")
    lottery = relationship("Lottery", back_populates="tickets", lazy="selectin")
    user = relationship("User", lazy="selectin")
    winner = relationship("LotteryWinner", back_populates="ticket", uselist=False, lazy="selectin")


class LotteryWinner(Base):
    __tablename__ = "lottery_winners"
    __table_args__ = (
        UniqueConstraint("ticket_id", name="uq_lottery_winner_ticket"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lottery_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lotteries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    prize_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lottery_prizes.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    ticket_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lottery_tickets.id", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    selection_method: Mapped[LotteryWinnerSelectionMethod] = mapped_column(
        Enum(
            LotteryWinnerSelectionMethod,
            name="lottery_winner_selection_method",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    status: Mapped[LotteryWinnerStatus] = mapped_column(
        Enum(
            LotteryWinnerStatus,
            name="lottery_winner_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=LotteryWinnerStatus.PENDING,
        index=True,
        nullable=False,
    )
    selected_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now(), nullable=False
    )
    confirmed_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    wallet_transaction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("wallet_transactions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    claim_contact: Mapped[str | None] = mapped_column(String(300), nullable=True)
    confirmation_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    lottery = relationship("Lottery", back_populates="winners", lazy="selectin")
    prize = relationship("LotteryPrize", back_populates="winners", lazy="selectin")
    ticket = relationship("LotteryTicket", back_populates="winner", lazy="selectin")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    selected_by = relationship("User", foreign_keys=[selected_by_user_id], lazy="selectin")
    confirmed_by = relationship("User", foreign_keys=[confirmed_by_user_id], lazy="selectin")
    wallet_transaction = relationship("WalletTransaction", lazy="selectin")
