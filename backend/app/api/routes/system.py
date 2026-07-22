"""Безопасные публичные параметры, необходимые frontend-приложениям."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.system import PublicSystemConfigRead

router = APIRouter(prefix="/system", tags=["Система"])


@router.get("/config", response_model=PublicSystemConfigRead)
async def get_public_system_config() -> PublicSystemConfigRead:
    """Возвращает только публичные лимиты и сроки, без ключей и секретов."""
    return PublicSystemConfigRead.from_settings(get_settings())
