"""Схемы новостей."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.db.enums import PostStatus
from app.schemas.common import APIModel


class PostCreate(APIModel):
    title: str = Field(min_length=1, max_length=250)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=250)
    excerpt: str = Field(default="", max_length=1000)
    content: str = Field(min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=1000)


class PostUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=250)
    excerpt: str | None = Field(default=None, max_length=1000)
    content: str | None = Field(default=None, min_length=1)
    cover_image_url: str | None = Field(default=None, max_length=1000)


class PostRead(APIModel):
    id: UUID
    author_id: UUID
    title: str
    slug: str
    excerpt: str
    content: str
    cover_image_url: str | None
    status: PostStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
