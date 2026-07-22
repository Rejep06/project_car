"""Публичные новости и административное управление публикациями."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.enums import PostStatus
from app.db.models import Post
from app.schemas.post import PostCreate, PostUpdate
from app.utils.datetime import utcnow


class PostService:
    @staticmethod
    async def list_public(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[Post], int]:
        condition = Post.status == PostStatus.PUBLISHED
        items = list(
            (
                await session.scalars(
                    select(Post)
                    .where(condition)
                    .order_by(Post.published_at.desc(), Post.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(select(func.count()).select_from(Post).where(condition)) or 0
        )
        return items, total

    @staticmethod
    async def get_public(session: AsyncSession, slug: str) -> Post:
        post = await session.scalar(
            select(Post).where(Post.slug == slug, Post.status == PostStatus.PUBLISHED)
        )
        if post is None:
            raise AppError("post_not_found", "Новость не найдена", status_code=404)
        return post

    @staticmethod
    async def get_admin(session: AsyncSession, post_id: UUID) -> Post:
        post = await session.get(Post, post_id)
        if post is None:
            raise AppError("post_not_found", "Новость не найдена", status_code=404)
        return post

    @staticmethod
    async def list_admin(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[Post], int]:
        items = list(
            (
                await session.scalars(
                    select(Post).order_by(Post.created_at.desc()).offset(offset).limit(limit)
                )
            ).all()
        )
        total = int(await session.scalar(select(func.count()).select_from(Post)) or 0)
        return items, total

    @staticmethod
    async def create(session: AsyncSession, *, data: PostCreate, author_id: UUID) -> Post:
        post = Post(author_id=author_id, **data.model_dump(), status=PostStatus.DRAFT)
        session.add(post)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError("post_slug_exists", "Новость с таким slug уже существует", status_code=409) from exc
        await session.refresh(post)
        return post

    @staticmethod
    async def update(session: AsyncSession, *, post_id: UUID, data: PostUpdate) -> Post:
        post = await session.scalar(select(Post).where(Post.id == post_id).with_for_update())
        if post is None:
            raise AppError("post_not_found", "Новость не найдена", status_code=404)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(post, field, value)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError("post_slug_exists", "Новость с таким slug уже существует", status_code=409) from exc
        await session.refresh(post)
        return post

    @staticmethod
    async def publish(session: AsyncSession, post_id: UUID) -> Post:
        post = await session.scalar(select(Post).where(Post.id == post_id).with_for_update())
        if post is None:
            raise AppError("post_not_found", "Новость не найдена", status_code=404)
        post.status = PostStatus.PUBLISHED
        post.published_at = utcnow()
        await session.commit()
        await session.refresh(post)
        return post

    @staticmethod
    async def archive(session: AsyncSession, post_id: UUID) -> Post:
        post = await session.scalar(select(Post).where(Post.id == post_id).with_for_update())
        if post is None:
            raise AppError("post_not_found", "Новость не найдена", status_code=404)
        post.status = PostStatus.ARCHIVED
        await session.commit()
        await session.refresh(post)
        return post
