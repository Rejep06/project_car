"""Формирование стабильного адреса публикации из её заголовка."""

from __future__ import annotations

import re
import unicodedata


_CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def make_post_slug(title: str, suffix: str, *, max_length: int = 250) -> str:
    """Возвращает URL-часть вида ``novosti-kompanii-a1b2c3d4``."""
    normalized = unicodedata.normalize("NFKD", title.strip().lower())
    transliterated = normalized.translate(_CYRILLIC_TO_LATIN)
    base = re.sub(r"[^a-z0-9]+", "-", transliterated).strip("-")
    if not base:
        base = "publication"
    clean_suffix = re.sub(r"[^a-z0-9]", "", suffix.lower())[:16] or "item"
    base_limit = max(1, max_length - len(clean_suffix) - 1)
    base = base[:base_limit].rstrip("-") or "publication"
    return f"{base}-{clean_suffix}"
