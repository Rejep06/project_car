"""Публичные настройки интерфейса без серверных секретов."""

from app.core.config import Settings
from app.schemas.common import APIModel


class PublicSystemConfigRead(APIModel):
    app_name: str
    asset: str
    network: str
    min_deposit_amount: str
    deposit_invoice_ttl_minutes: int
    deposit_amount_reservation_hours: int
    min_withdrawal_amount: str
    withdrawal_fee: str
    support_max_file_size_mb: int
    support_max_files_per_message: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "PublicSystemConfigRead":
        return cls(
            app_name=settings.app_name,
            asset=settings.asset,
            network=settings.network_display_name,
            min_deposit_amount=settings.min_deposit_amount,
            deposit_invoice_ttl_minutes=settings.deposit_invoice_ttl_minutes,
            deposit_amount_reservation_hours=settings.deposit_amount_reservation_hours,
            min_withdrawal_amount=settings.min_withdrawal_amount,
            withdrawal_fee=settings.withdrawal_fee,
            support_max_file_size_mb=settings.support_max_file_size_mb,
            support_max_files_per_message=settings.support_max_files_per_message,
        )
