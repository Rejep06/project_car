"""Публичные настройки клиентского интерфейса без секретов."""

from datetime import datetime

from app.core.config import Settings
from app.schemas.common import APIModel
from app.utils.datetime import get_withdrawal_window


class PublicSystemConfigRead(APIModel):
    app_name: str
    asset: str
    network: str
    min_deposit_amount: str
    deposit_invoice_ttl_minutes: int
    deposit_amount_reservation_hours: int
    min_withdrawal_amount: str
    withdrawal_fee: str
    withdrawal_is_open: bool
    withdrawal_timezone: str
    withdrawal_weekday_label: str
    next_withdrawal_open_at: datetime | None
    withdrawal_processing_min_hours: int
    withdrawal_processing_max_days: int
    referral_purchase_bonus_percent: int
    premium_referral_reward_bonus: str
    support_max_file_size_mb: int
    support_max_files_per_message: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "PublicSystemConfigRead":
        window = get_withdrawal_window(
            timezone_name=settings.business_timezone,
            allowed_weekday=settings.withdrawal_allowed_weekday,
        )
        return cls(
            app_name=settings.app_name,
            asset=settings.asset,
            network=settings.network_display_name,
            min_deposit_amount=settings.min_deposit_amount,
            deposit_invoice_ttl_minutes=settings.deposit_invoice_ttl_minutes,
            deposit_amount_reservation_hours=settings.deposit_amount_reservation_hours,
            min_withdrawal_amount=settings.min_withdrawal_amount,
            withdrawal_fee=settings.withdrawal_fee,
            withdrawal_is_open=window.is_open,
            withdrawal_timezone=window.timezone,
            withdrawal_weekday_label=window.weekday_label,
            next_withdrawal_open_at=window.next_open_at,
            withdrawal_processing_min_hours=settings.withdrawal_processing_min_hours,
            withdrawal_processing_max_days=settings.withdrawal_processing_max_days,
            referral_purchase_bonus_percent=settings.referral_purchase_bonus_percent,
            premium_referral_reward_bonus=settings.premium_referral_reward_bonus,
            support_max_file_size_mb=settings.support_max_file_size_mb,
            support_max_files_per_message=settings.support_max_files_per_message,
        )
