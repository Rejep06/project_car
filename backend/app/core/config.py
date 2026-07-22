"""Настройки приложения, загружаемые из переменных окружения."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.money import parse_amount


class Settings(BaseSettings):
    """Единая типизированная конфигурация backend-приложения."""

    app_name: str = "Subscription Platform"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/subscriptions"

    jwt_secret: str = "change-me"
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=30, ge=1)

    asset: Literal["USDT"] = "USDT"
    asset_decimals: int = Field(default=6, ge=6, le=6)
    network: Literal["TRON"] = "TRON"
    network_display_name: str = "TRON (TRC20)"

    binance_api_base_url: str = "https://api.binance.com"
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_deposit_address: str = ""
    binance_enabled: bool = True
    binance_request_timeout_seconds: float = Field(default=15.0, gt=0)
    binance_lookback_hours: int = Field(default=24, ge=1, le=2160)

    min_deposit_amount: str = "10.000000"
    deposit_invoice_ttl_minutes: int = Field(default=30, ge=1)
    deposit_amount_reservation_hours: int = Field(default=24, ge=24)
    deposit_poll_interval_seconds: int = Field(default=20, ge=1)

    min_withdrawal_amount: str = "20.000000"
    withdrawal_fee: str = "2.000000"

    reward_worker_interval_seconds: int = Field(default=30, ge=1)
    reward_worker_batch_size: int = Field(default=50, ge=1, le=500)

    support_upload_dir: str = "uploads/support"
    support_max_file_size_mb: int = Field(default=5, ge=1, le=5)
    support_max_files_per_message: int = Field(default=3, ge=1, le=3)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Проверяет критичные ограничения и production-секреты."""
        if self.asset_decimals != 6:
            raise ValueError("Проект поддерживает только 6 знаков USDT")
        if self.asset.upper() != "USDT":
            raise ValueError("Проект поддерживает только USDT")
        if self.network.upper() != "TRON":
            raise ValueError("Проект поддерживает только сеть TRON")

        # Проверяем денежные строки при старте, чтобы ошибка не проявилась позднее.
        min_deposit = parse_amount(self.min_deposit_amount)
        min_withdrawal = parse_amount(self.min_withdrawal_amount)
        withdrawal_fee = parse_amount(self.withdrawal_fee)
        if min_deposit <= 0 or min_withdrawal <= 0:
            raise ValueError("Минимальные суммы должны быть больше нуля")
        if withdrawal_fee < 0:
            raise ValueError("Комиссия вывода не может быть отрицательной")
        if (
            self.deposit_amount_reservation_hours * 60
            <= self.deposit_invoice_ttl_minutes
        ):
            raise ValueError(
                "Резервирование точной суммы должно продолжаться после срока заявки"
            )

        origins = self.cors_origin_list
        if self.app_env == "production" and "*" in origins:
            raise ValueError("В production CORS_ORIGINS не может содержать *")

        if self.app_env == "production":
            if not self.jwt_secret or self.jwt_secret == "change-me":
                raise ValueError("В production необходимо задать безопасный JWT_SECRET")
            if self.binance_enabled and (
                not self.binance_api_key
                or not self.binance_api_secret
                or not self.binance_deposit_address
            ):
                raise ValueError(
                    "Для включённой Binance-интеграции в production нужны API key, secret и адрес"
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """Возвращает разрешённые browser origins без пустых значений."""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def min_deposit_amount_atomic(self) -> int:
        return parse_amount(self.min_deposit_amount)

    @property
    def min_withdrawal_amount_atomic(self) -> int:
        return parse_amount(self.min_withdrawal_amount)

    @property
    def withdrawal_fee_atomic(self) -> int:
        return parse_amount(self.withdrawal_fee)

    @property
    def support_max_file_size_bytes(self) -> int:
        return self.support_max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает закэшированный объект настроек."""
    return Settings()
