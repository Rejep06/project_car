"""Безопасная проверка и локальное хранение вложений поддержки."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import AppError

ALLOWED_FILE_TYPES: dict[str, set[str]] = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
    ".pdf": {"application/pdf"},
}


@dataclass(frozen=True, slots=True)
class StoredFile:
    original_filename: str
    stored_filename: str
    mime_type: str
    size_bytes: int
    file_path: str


def _content_matches(extension: str, content: bytes) -> bool:
    """Проверяет сигнатуру поддерживаемого формата без тяжёлого OCR/парсинга."""
    if extension == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if extension == ".webp":
        return len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    if extension == ".pdf":
        return content.startswith(b"%PDF-")
    return False


async def store_support_upload(
    upload: UploadFile,
    *,
    upload_dir: str,
    max_size_bytes: int,
) -> StoredFile:
    """Проверяет файл и сохраняет его под случайным UUID-именем."""
    original_name = Path(upload.filename or "file").name
    extension = Path(original_name).suffix.lower()
    mime_type = (upload.content_type or "").lower()

    if extension not in ALLOWED_FILE_TYPES or mime_type not in ALLOWED_FILE_TYPES[extension]:
        raise AppError(
            "unsupported_file_type",
            "Разрешены только PNG, JPG, JPEG, WEBP и PDF",
            status_code=415,
        )

    content = await upload.read(max_size_bytes + 1)
    await upload.close()
    if len(content) > max_size_bytes:
        raise AppError(
            "file_too_large",
            "Размер файла превышает допустимый лимит",
            status_code=413,
        )
    if not content or not _content_matches(extension, content):
        raise AppError(
            "invalid_file_content",
            "Содержимое файла не соответствует расширению",
            status_code=415,
        )

    root = Path(upload_dir).resolve()
    await asyncio.to_thread(root.mkdir, mode=0o750, parents=True, exist_ok=True)
    await asyncio.to_thread(root.chmod, 0o750)
    stored_filename = f"{uuid4().hex}{extension}"
    target = (root / stored_filename).resolve()
    if not target.is_relative_to(root):
        raise AppError("invalid_file_path", "Недопустимый путь файла", status_code=400)
    await asyncio.to_thread(target.write_bytes, content)
    await asyncio.to_thread(target.chmod, 0o640)

    return StoredFile(
        original_filename=original_name[:255],
        stored_filename=stored_filename,
        mime_type=mime_type,
        size_bytes=len(content),
        file_path=str(target),
    )


def resolve_attachment_path(file_path: str, upload_dir: str) -> Path:
    """Возвращает только путь внутри разрешённой директории."""
    root = Path(upload_dir).resolve()
    target = Path(file_path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise AppError("attachment_not_found", "Вложение не найдено", status_code=404)
    return target
