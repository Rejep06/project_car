"""Клиент Binance только для чтения истории депозитов."""

import time
from datetime import datetime

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.integrations.binance.schemas import BinanceDepositData
from app.integrations.binance.signature import with_signature


class BinanceReadOnlyClient:
    """Клиент использует только endpoint чтения истории пополнений."""

    DEPOSIT_HISTORY_PATH = "/sapi/v1/capital/deposit/hisrec"

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http_client = http_client

    async def get_deposit_history(
        self,
        start_time: datetime | None = None,
    ) -> list[BinanceDepositData]:
        """Получает и нормализует до 1000 последних депозитов."""
        if not self.settings.binance_api_key or not self.settings.binance_api_secret:
            raise AppError(
                "binance_not_configured",
                "Binance API-ключи не настроены",
                status_code=503,
            )
        params: dict[str, str | int] = {
            "timestamp": int(time.time() * 1000),
            "recvWindow": 10_000,
            "limit": 1000,
        }
        if start_time is not None:
            params["startTime"] = int(start_time.timestamp() * 1000)
        signed_params = with_signature(params, self.settings.binance_api_secret)
        headers = {"X-MBX-APIKEY": self.settings.binance_api_key}

        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(
            base_url=self.settings.binance_api_base_url,
            timeout=self.settings.binance_request_timeout_seconds,
        )
        try:
            response = await client.get(
                self.DEPOSIT_HISTORY_PATH,
                params=signed_params,
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AppError(
                "binance_api_error",
                "Не удалось получить историю депозитов Binance",
                status_code=502,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

        if not isinstance(payload, list):
            raise AppError(
                "binance_invalid_response",
                "Binance вернул неожиданный формат данных",
                status_code=502,
            )
        return [BinanceDepositData.from_api(item) for item in payload if isinstance(item, dict)]
