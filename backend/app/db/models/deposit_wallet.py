"""Адреса пополнения и параметры их автоматической проверки."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.config import USDT_ETHEREUM_CONTRACT
from app.db.base import Base, TimestampMixin


class DepositWallet(TimestampMixin, Base):
    """Кошелёк, который администратор может опубликовать для клиентов.

    Модель не привязана к одной сети: произвольный адрес можно хранить с
    ``monitoring_enabled=False``. Автоматическая проверка в текущей версии
    поддерживает Infura + EVM + ERC-20.
    """

    __tablename__ = "deposit_wallets"
    __table_args__ = (
        UniqueConstraint("network", "address", name="uq_deposit_wallet_network_address"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    asset: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    network: Mapped[str] = mapped_column(String(64), default="ETHEREUM", nullable=False)
    network_display_name: Mapped[str] = mapped_column(
        String(100), default="Ethereum (ERC-20)", nullable=False
    )
    address: Mapped[str] = mapped_column(String(256), nullable=False)

    provider: Mapped[str] = mapped_column(String(40), default="infura", nullable=False)
    provider_network: Mapped[str | None] = mapped_column(
        String(80), default="mainnet", nullable=True
    )
    chain_id: Mapped[int | None] = mapped_column(Integer, default=1, nullable=True)
    token_standard: Mapped[str | None] = mapped_column(
        String(32), default="ERC20", nullable=True
    )
    token_contract_address: Mapped[str | None] = mapped_column(
        String(256), default=USDT_ETHEREUM_CONTRACT, nullable=True
    )
    token_decimals: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    confirmations_required: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    monitoring_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, index=True, nullable=False
    )

    deposit_invoices = relationship("DepositInvoice", back_populates="deposit_wallet", lazy="raise")
