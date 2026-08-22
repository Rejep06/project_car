"""Схемы адресов пополнения и параметров мониторинга."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.core.config import USDT_ETHEREUM_CONTRACT
from app.schemas.common import (
    APIModel,
    validate_evm_address,
    validate_generic_wallet_address,
)


class DepositWalletBase(APIModel):
    title: str = Field(min_length=2, max_length=120)
    address: str
    asset: str = Field(default="USDT", min_length=2, max_length=16)
    network: str = Field(default="ETHEREUM", min_length=2, max_length=64)
    network_display_name: str = Field(
        default="Ethereum (ERC-20)", min_length=2, max_length=100
    )

    provider: str = Field(default="infura", min_length=2, max_length=40)
    provider_network: str | None = Field(default="mainnet", max_length=80)
    chain_id: int | None = Field(default=1, ge=1)
    token_standard: str | None = Field(default="ERC20", max_length=32)
    token_contract_address: str | None = Field(
        default=USDT_ETHEREUM_CONTRACT, max_length=256
    )
    token_decimals: int = Field(default=6, ge=0, le=18)
    confirmations_required: int = Field(default=12, ge=0, le=10000)
    monitoring_enabled: bool = True

    sort_order: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        return validate_generic_wallet_address(value)

    @field_validator("asset", "network")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("provider_network")
    @classmethod
    def normalize_provider_network(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    @field_validator("token_standard")
    @classmethod
    def normalize_standard(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None

    @model_validator(mode="after")
    def validate_monitoring_configuration(self) -> "DepositWalletBase":
        if self.asset != "USDT":
            raise ValueError("Текущая версия принимает пополнения только в USDT")
        if self.token_decimals != 6:
            raise ValueError("Суммы USDT в проекте хранятся с 6 знаками после запятой")
        if not self.monitoring_enabled:
            return self
        if self.provider != "infura":
            raise ValueError(
                "Автоматическая проверка пока поддерживает только провайдер Infura"
            )
        if not self.provider_network:
            raise ValueError("Для Infura укажите сеть провайдера, например mainnet")
        if self.provider_network != "mainnet":
            raise ValueError(
                "Автоматическая проверка пока работает только в Ethereum Mainnet"
            )
        if self.chain_id is None:
            raise ValueError("Для автоматической проверки необходимо указать chain ID")
        if self.chain_id != 1:
            raise ValueError(
                "Автоматическая проверка Ethereum Mainnet требует chain ID 1"
            )
        if self.network != "ETHEREUM":
            raise ValueError(
                "Автоматическая проверка пока поддерживает только сеть Ethereum"
            )
        if self.token_standard != "ERC20":
            raise ValueError("Автоматическая проверка пока поддерживает только ERC-20")
        if self.confirmations_required < 1:
            raise ValueError(
                "Для автоматической проверки требуется минимум одно подтверждение"
            )
        if not self.token_contract_address:
            raise ValueError("Укажите адрес контракта токена ERC-20")
        self.address = validate_evm_address(self.address)
        self.token_contract_address = validate_evm_address(
            self.token_contract_address
        )
        if self.token_contract_address != USDT_ETHEREUM_CONTRACT:
            raise ValueError(
                "Для автоматической проверки используйте официальный контракт "
                "USDT ERC-20 в Ethereum"
            )
        return self


class DepositWalletCreate(DepositWalletBase):
    pass


class DepositWalletUpdate(APIModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    address: str | None = None
    asset: str | None = Field(default=None, min_length=2, max_length=16)
    network: str | None = Field(default=None, min_length=2, max_length=64)
    network_display_name: str | None = Field(default=None, min_length=2, max_length=100)
    provider: str | None = Field(default=None, min_length=2, max_length=40)
    provider_network: str | None = Field(default=None, max_length=80)
    chain_id: int | None = Field(default=None, ge=1)
    token_standard: str | None = Field(default=None, max_length=32)
    token_contract_address: str | None = Field(default=None, max_length=256)
    token_decimals: int | None = Field(default=None, ge=0, le=18)
    confirmations_required: int | None = Field(default=None, ge=0, le=10000)
    monitoring_enabled: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    is_active: bool | None = None

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str | None) -> str | None:
        return validate_generic_wallet_address(value) if value is not None else None

    @field_validator("asset", "network")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("provider")
    @classmethod
    def normalize_provider(cls, value: str | None) -> str | None:
        return value.strip().lower() if value is not None else None

    @field_validator("provider_network")
    @classmethod
    def normalize_provider_network(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else None

    @field_validator("token_standard")
    @classmethod
    def normalize_standard(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class DepositWalletPublicRead(APIModel):
    id: UUID
    title: str
    address: str
    asset: str
    network: str
    network_display_name: str
    sort_order: int
    is_active: bool


class DepositWalletRead(DepositWalletPublicRead):
    provider: str
    provider_network: str | None
    chain_id: int | None
    token_standard: str | None
    token_contract_address: str | None
    token_decimals: int
    confirmations_required: int
    monitoring_enabled: bool
    created_at: datetime
    updated_at: datetime
