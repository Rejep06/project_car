"""Настройки приложения, загружаемые из переменных окружения."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.money import parse_amount


USDT_ETHEREUM_CONTRACT = "0xdac17f958d2ee523a2206206994597c13d831ec7"


class Settings(BaseSettings):
    """Единая типизированная конфигурация backend-приложения."""

    app_name: str = "Subscription Platform"
    app_env: Literal["development", "test", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    customer_frontend_url: str = "http://localhost:3000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/subscriptions"

    jwt_secret: str = "change-me"
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=30, ge=1)

    # Подтверждение email и восстановление пароля.
    email_delivery_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Automotive Club"
    smtp_starttls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    email_verification_ttl_hours: int = Field(default=24, ge=1, le=168)
    password_reset_ttl_minutes: int = Field(default=60, ge=5, le=1440)
    email_request_cooldown_seconds: int = Field(default=60, ge=0, le=3600)
    email_worker_interval_seconds: int = Field(default=10, ge=1, le=3600)
    email_worker_batch_size: int = Field(default=20, ge=1, le=200)
    email_worker_max_attempts: int = Field(default=8, ge=1, le=50)

    # Версии юридических документов и формы акцепта фиксируются вместе
    # с согласием. При изменении текста документов увеличьте соответствующую
    # версию в production .env.
    registration_consent_form_version: str = "2026-08-10"
    terms_version: str = "2026-08-10"
    privacy_policy_version: str = "2026-08-10"
    personal_data_processing_version: str = "2026-08-10"
    program_rules_version: str = "2026-08-10"
    age_confirmation_version: str = "2026-08-10"

    # Текущая клиентская валюта и сеть вывода. Адреса пополнения при этом
    # хранят собственные параметры сети и могут быть добавлены отдельно.
    asset: str = "USDT"
    asset_decimals: int = Field(default=6, ge=0, le=18)
    network: str = "ETHEREUM"
    network_display_name: str = "Ethereum (ERC-20)"

    # Универсальный адрес по умолчанию. При первом запуске он переносится в БД.
    default_deposit_address: str = ""

    # Автоматическая проверка переводов. Сейчас реализована первая интеграция:
    # Ethereum JSON-RPC через Infura и события Transfer токена USDT ERC-20.
    deposit_monitoring_enabled: bool = True
    infura_api_key: str = ""
    infura_jwt: str = ""
    infura_rpc_url: str = ""
    infura_request_timeout_seconds: float = Field(default=30.0, gt=0, le=600)

    ethereum_provider_network: str = "mainnet"
    ethereum_chain_id: int = Field(default=1, ge=1)
    ethereum_usdt_contract_address: str = USDT_ETHEREUM_CONTRACT
    ethereum_usdt_decimals: int = Field(default=6, ge=0, le=18)
    ethereum_confirmations: int = Field(default=12, ge=1, le=10000)
    ethereum_initial_lookback_blocks: int = Field(default=0, ge=0, le=2_000_000)
    ethereum_reorg_lookback_blocks: int = Field(default=1, ge=0, le=10000)
    ethereum_log_block_range: int = Field(default=1000, ge=1, le=100_000)
    ethereum_address_batch_size: int = Field(default=50, ge=1, le=500)

    min_deposit_amount: str = "10.000000"
    deposit_invoice_ttl_minutes: int = Field(default=30, ge=1)
    deposit_amount_reservation_hours: int = Field(default=24, ge=24)
    deposit_poll_interval_seconds: int = Field(default=300, ge=1)

    min_withdrawal_amount: str = "20.000000"
    withdrawal_fee: str = "2.000000"
    business_timezone: str = "Asia/Almaty"
    withdrawal_allowed_weekday: int = Field(default=2, ge=-1, le=6)
    withdrawal_processing_min_hours: int = Field(default=1, ge=1, le=72)
    withdrawal_processing_max_days: int = Field(default=3, ge=1, le=30)

    referral_purchase_bonus_percent: int = Field(default=10, ge=0, le=100)
    premium_referral_reward_bonus: str = "2.000000"

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

    @field_validator("smtp_host", mode="before")
    @classmethod
    def normalize_smtp_host(cls, value: object) -> str:
        """Нормализует SMTP hostname и отсекает URL/host:port из .env."""
        if value is None:
            return ""
        host = str(value).strip()
        if not host:
            return ""
        if "://" in host or any(char in host for char in "/?#"):
            raise ValueError(
                "SMTP_HOST должен содержать только имя сервера, например "
                "smtp-relay.brevo.com, без протокола и пути"
            )
        if any(char.isspace() for char in host):
            raise ValueError("SMTP_HOST не должен содержать пробелы")

        # Квадратные скобки допустимы только как оболочка IPv6-адреса.
        if host.startswith("[") and host.endswith("]"):
            host = host[1:-1]
        elif ":" in host:
            # Наиболее частая ошибка — SMTP_HOST=smtp.example.com:587.
            # Порт должен храниться отдельно в SMTP_PORT. IPv6 без скобок
            # оставляем допустимым.
            try:
                import ipaddress

                ipaddress.ip_address(host)
            except ValueError as exc:
                raise ValueError(
                    "Не добавляйте порт в SMTP_HOST; используйте SMTP_PORT"
                ) from exc

        return host.rstrip(".").lower()

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Проверяет критичные ограничения и production-секреты."""
        if self.asset_decimals != 6 or self.ethereum_usdt_decimals != 6:
            raise ValueError("USDT в проекте должен храниться с 6 знаками после запятой")
        if self.asset.strip().upper() != "USDT":
            raise ValueError("Текущая версия проекта поддерживает расчёты только в USDT")
        if self.network.strip().upper() != "ETHEREUM":
            raise ValueError(
                "Текущая автоматическая сеть проекта должна быть ETHEREUM"
            )
        if self.ethereum_provider_network.strip().lower() != "mainnet":
            raise ValueError(
                "Автоматическая проверка сейчас поддерживает только Ethereum Mainnet"
            )
        if self.ethereum_chain_id != 1:
            raise ValueError("Для Ethereum Mainnet необходимо ETHEREUM_CHAIN_ID=1")
        if (
            self.ethereum_usdt_contract_address.strip().lower()
            != USDT_ETHEREUM_CONTRACT
        ):
            raise ValueError(
                "ETHEREUM_USDT_CONTRACT_ADDRESS должен содержать официальный "
                "контракт USDT ERC-20"
            )

        min_deposit = parse_amount(self.min_deposit_amount)
        min_withdrawal = parse_amount(self.min_withdrawal_amount)
        withdrawal_fee = parse_amount(self.withdrawal_fee)
        premium_referral_bonus = parse_amount(self.premium_referral_reward_bonus)
        if min_deposit <= 0 or min_withdrawal <= 0:
            raise ValueError("Минимальные суммы должны быть больше нуля")
        if withdrawal_fee < 0:
            raise ValueError("Комиссия вывода не может быть отрицательной")
        if premium_referral_bonus < 0:
            raise ValueError("Реферальный бонус не может быть отрицательным")
        if self.deposit_amount_reservation_hours * 60 <= self.deposit_invoice_ttl_minutes:
            raise ValueError(
                "Резервирование точной суммы должно продолжаться после срока заявки"
            )
        if self.smtp_use_ssl and self.smtp_starttls:
            raise ValueError("Нельзя одновременно включать SMTP_USE_SSL и SMTP_STARTTLS")
        if self.email_delivery_enabled:
            required_email_settings = {
                "SMTP_HOST": self.smtp_host,
                "SMTP_FROM_EMAIL": self.smtp_from_email,
                "CUSTOMER_FRONTEND_URL": self.customer_frontend_url,
            }
            missing = [
                name
                for name, value in required_email_settings.items()
                if not value.strip()
            ]
            if missing:
                raise ValueError(
                    "Для отправки писем задайте: " + ", ".join(missing)
                )

        origins = self.cors_origin_list
        if self.app_env == "production" and "*" in origins:
            raise ValueError("В production CORS_ORIGINS не может содержать *")

        if self.app_env == "production":
            if not self.jwt_secret or self.jwt_secret == "change-me":
                raise ValueError("В production необходимо задать безопасный JWT_SECRET")
            if self.deposit_monitoring_enabled and not (
                self.infura_api_key.strip() or self.infura_rpc_url.strip()
            ):
                raise ValueError(
                    "Для автоматической проверки пополнений в production задайте "
                    "INFURA_API_KEY или INFURA_RPC_URL"
                )
            if not self.email_delivery_enabled:
                raise ValueError(
                    "В production подтверждение email требует EMAIL_DELIVERY_ENABLED=true"
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def frontend_base_url(self) -> str:
        return self.customer_frontend_url.rstrip("/")

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
    def premium_referral_reward_bonus_atomic(self) -> int:
        return parse_amount(self.premium_referral_reward_bonus)

    @property
    def support_max_file_size_bytes(self) -> int:
        return self.support_max_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает закэшированный объект настроек."""
    return Settings()
