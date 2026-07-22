"""Подпись HMAC SHA-256 для Binance SIGNED endpoints."""

import hashlib
import hmac
from collections.abc import Mapping
from urllib.parse import urlencode


def sign_query(params: Mapping[str, str | int], api_secret: str) -> str:
    """Возвращает hex-подпись точной query string."""
    query = urlencode(list(params.items()))
    return hmac.new(
        api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def with_signature(
    params: Mapping[str, str | int], api_secret: str
) -> dict[str, str | int]:
    """Создаёт новую коллекцию параметров с полем signature."""
    signed = dict(params)
    signed["signature"] = sign_query(signed, api_secret)
    return signed
