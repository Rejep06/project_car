"""Минимальная настройка структурированного системного логирования."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Настраивает единый формат логов без вывода секретов и payload запросов."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
