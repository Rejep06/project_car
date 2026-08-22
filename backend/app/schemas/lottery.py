"""Схемы публичных и административных операций с лотереями."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.db.enums import (
    LotteryPrizeType,
    LotteryStatus,
    LotteryTicketStatus,
    LotteryWinnerSelectionMethod,
    LotteryWinnerStatus,
)
from app.schemas.common import APIModel
from app.utils.datetime import ensure_utc, utcnow
from app.utils.money import MoneyFormatError, format_amount, parse_amount


def _positive_money(value: str) -> str:
    try:
        atomic = parse_amount(value)
    except MoneyFormatError as exc:
        raise ValueError(str(exc)) from exc
    if atomic <= 0:
        raise ValueError("Сумма должна быть больше нуля")
    return format_amount(atomic)


class LotteryPrizeCreate(APIModel):
    title: str = Field(min_length=2, max_length=250)
    description: str = Field(default="", max_length=5000)
    prize_type: LotteryPrizeType
    amount: str | None = None
    quantity: int = Field(default=1, ge=1, le=1000)
    sort_order: int = Field(default=0, ge=0, le=100000)
    image_url: str | None = Field(default=None, max_length=1000)
    manager_telegram: str | None = Field(default=None, max_length=120)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str | None) -> str | None:
        return _positive_money(value) if value is not None else None

    @model_validator(mode="after")
    def validate_prize(self) -> "LotteryPrizeCreate":
        if self.prize_type == LotteryPrizeType.BALANCE and self.amount is None:
            raise ValueError("Для денежного приза укажите сумму")
        if self.prize_type == LotteryPrizeType.PHYSICAL and self.amount is not None:
            raise ValueError("Для неденежного приза сумма не указывается")
        return self


class LotteryPrizeUpdate(APIModel):
    title: str | None = Field(default=None, min_length=2, max_length=250)
    description: str | None = Field(default=None, max_length=5000)
    prize_type: LotteryPrizeType | None = None
    amount: str | None = None
    quantity: int | None = Field(default=None, ge=1, le=1000)
    sort_order: int | None = Field(default=None, ge=0, le=100000)
    image_url: str | None = Field(default=None, max_length=1000)
    manager_telegram: str | None = Field(default=None, max_length=120)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str | None) -> str | None:
        return _positive_money(value) if value is not None else None


class LotteryCreate(APIModel):
    title: str = Field(min_length=3, max_length=250)
    description: str = Field(min_length=10, max_length=30000)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    ticket_price: str
    sales_start_at: datetime
    sales_end_at: datetime
    draw_at: datetime
    max_tickets_total: int | None = Field(default=None, ge=1, le=10_000_000)
    max_tickets_per_user: int = Field(default=20, ge=1, le=10000)
    manager_telegram: str | None = Field(default=None, max_length=120)
    rules_text: str = Field(min_length=20, max_length=50000)
    rules_version: str = Field(default="1.0", min_length=1, max_length=40)

    @field_validator("ticket_price")
    @classmethod
    def validate_ticket_price(cls, value: str) -> str:
        return _positive_money(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "LotteryCreate":
        start = ensure_utc(self.sales_start_at)
        end = ensure_utc(self.sales_end_at)
        draw = ensure_utc(self.draw_at)
        if start >= end:
            raise ValueError("Начало продаж должно быть раньше дедлайна")
        if end > draw:
            raise ValueError("Дата результатов не может быть раньше дедлайна")
        return self


class LotteryUpdate(APIModel):
    title: str | None = Field(default=None, min_length=3, max_length=250)
    description: str | None = Field(default=None, min_length=10, max_length=30000)
    cover_image_url: str | None = Field(default=None, max_length=1000)
    ticket_price: str | None = None
    sales_start_at: datetime | None = None
    sales_end_at: datetime | None = None
    draw_at: datetime | None = None
    max_tickets_total: int | None = Field(default=None, ge=1, le=10_000_000)
    max_tickets_per_user: int | None = Field(default=None, ge=1, le=10000)
    manager_telegram: str | None = Field(default=None, max_length=120)
    rules_text: str | None = Field(default=None, min_length=20, max_length=50000)
    rules_version: str | None = Field(default=None, min_length=1, max_length=40)

    @field_validator("ticket_price")
    @classmethod
    def validate_ticket_price(cls, value: str | None) -> str | None:
        return _positive_money(value) if value is not None else None


class LotteryTicketPurchaseRequest(APIModel):
    quantity: int = Field(default=1, ge=1, le=100)
    accept_rules: Literal[True]


class LotteryManualWinnerRequest(APIModel):
    prize_id: UUID
    ticket_id: UUID


class LotteryWinnerConfirmRequest(APIModel):
    note: str | None = Field(default=None, max_length=2000)


class LotteryPrizeRead(APIModel):
    id: UUID
    title: str
    description: str
    prize_type: LotteryPrizeType
    amount: str | None
    asset: str = "USDT"
    quantity: int
    sort_order: int
    image_url: str | None
    manager_telegram: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_prize(cls, prize: object) -> "LotteryPrizeRead":
        amount_atomic = getattr(prize, "amount_atomic")
        return cls(
            id=getattr(prize, "id"),
            title=getattr(prize, "title"),
            description=getattr(prize, "description"),
            prize_type=getattr(prize, "prize_type"),
            amount=(format_amount(amount_atomic) if amount_atomic is not None else None),
            quantity=getattr(prize, "quantity"),
            sort_order=getattr(prize, "sort_order"),
            image_url=getattr(prize, "image_url"),
            manager_telegram=getattr(prize, "manager_telegram"),
            created_at=getattr(prize, "created_at"),
            updated_at=getattr(prize, "updated_at"),
        )


class LotteryWinnerPublicRead(APIModel):
    id: UUID
    prize_id: UUID
    prize_title: str
    ticket_code: str
    winner_email_masked: str
    confirmed_at: datetime


class LotterySummaryRead(APIModel):
    id: UUID
    title: str
    description: str
    cover_image_url: str | None
    status: LotteryStatus
    ticket_price: str
    asset: str = "USDT"
    sales_start_at: datetime
    sales_end_at: datetime
    draw_at: datetime
    sales_open: bool
    max_tickets_total: int | None
    max_tickets_per_user: int
    tickets_sold: int
    confirmed_winners_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_lottery(
        cls,
        lottery: object,
        *,
        tickets_sold: int,
        confirmed_winners_count: int,
    ) -> "LotterySummaryRead":
        now = utcnow()
        status = getattr(lottery, "status")
        sales_open = (
            status == LotteryStatus.PUBLISHED
            and ensure_utc(getattr(lottery, "sales_start_at")) <= now
            < ensure_utc(getattr(lottery, "sales_end_at"))
            and (
                getattr(lottery, "max_tickets_total") is None
                or tickets_sold < getattr(lottery, "max_tickets_total")
            )
        )
        return cls(
            id=getattr(lottery, "id"),
            title=getattr(lottery, "title"),
            description=getattr(lottery, "description"),
            cover_image_url=getattr(lottery, "cover_image_url"),
            status=status,
            ticket_price=format_amount(getattr(lottery, "ticket_price_atomic")),
            sales_start_at=getattr(lottery, "sales_start_at"),
            sales_end_at=getattr(lottery, "sales_end_at"),
            draw_at=getattr(lottery, "draw_at"),
            sales_open=sales_open,
            max_tickets_total=getattr(lottery, "max_tickets_total"),
            max_tickets_per_user=getattr(lottery, "max_tickets_per_user"),
            tickets_sold=tickets_sold,
            confirmed_winners_count=confirmed_winners_count,
            created_at=getattr(lottery, "created_at"),
            updated_at=getattr(lottery, "updated_at"),
        )


class LotteryDetailRead(LotterySummaryRead):
    manager_telegram: str | None
    rules_text: str
    rules_version: str
    prizes: list[LotteryPrizeRead]
    winners: list[LotteryWinnerPublicRead]


class LotteryTicketRead(APIModel):
    id: UUID
    lottery_id: UUID
    lottery_title: str
    ticket_code: str
    price: str
    asset: str = "USDT"
    status: LotteryTicketStatus
    purchased_at: datetime
    draw_at: datetime
    winner_status: LotteryWinnerStatus | None
    prize_title: str | None
    prize_type: LotteryPrizeType | None
    prize_amount: str | None
    claim_contact: str | None


class LotteryPurchaseRead(APIModel):
    purchase_id: UUID
    lottery_id: UUID
    quantity: int
    total_amount: str
    asset: str = "USDT"
    tickets: list[LotteryTicketRead]
    created_at: datetime


class LotteryAdminTicketRead(APIModel):
    id: UUID
    user_id: UUID
    user_email: str
    ticket_code: str
    status: LotteryTicketStatus
    purchased_at: datetime
    is_winner: bool


class LotteryWinnerAdminRead(APIModel):
    id: UUID
    lottery_id: UUID
    prize_id: UUID
    prize_title: str
    prize_type: LotteryPrizeType
    prize_amount: str | None
    ticket_id: UUID
    ticket_code: str
    user_id: UUID
    user_email: str
    selection_method: LotteryWinnerSelectionMethod
    status: LotteryWinnerStatus
    selected_at: datetime
    confirmed_at: datetime | None
    claim_contact: str | None
    confirmation_note: str | None


class LotteryAdminRead(LotteryDetailRead):
    created_by_user_id: UUID
    published_at: datetime | None
    completed_at: datetime | None
    pending_winners_count: int
    admin_winners: list[LotteryWinnerAdminRead]
