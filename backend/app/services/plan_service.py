"""Управление клиентскими программами без удаления уже активированных записей."""

from typing import Any
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.enums import PlanTier
from app.db.models import SubscriptionPlan
from app.schemas.plan import PlanCreate, PlanUpdate
from app.services.audit_service import AuditService
from app.utils.money import format_amount, parse_amount


TIER_ORDER = case(
    (SubscriptionPlan.tier == PlanTier.STARTER, 1),
    (SubscriptionPlan.tier == PlanTier.STANDARD, 2),
    (SubscriptionPlan.tier == PlanTier.PREMIUM, 3),
    else_=4,
)


def plan_snapshot(plan: SubscriptionPlan) -> dict[str, Any]:
    return {
        "title": plan.title,
        "tier": plan.tier.value,
        "short_description": plan.short_description,
        "image_url": plan.image_url,
        "price": format_amount(plan.price_atomic),
        "reward_amount": format_amount(plan.reward_amount_atomic),
        "reward_frequency": plan.reward_frequency.value,
        "is_active": plan.is_active,
    }


class PlanService:
    @staticmethod
    async def list_public(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[SubscriptionPlan], int]:
        condition = SubscriptionPlan.is_active.is_(True)
        items = list(
            (
                await session.scalars(
                    select(SubscriptionPlan)
                    .where(condition)
                    .order_by(TIER_ORDER, SubscriptionPlan.price_atomic)
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(SubscriptionPlan).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def get_public(session: AsyncSession, plan_id: UUID) -> SubscriptionPlan:
        plan = await session.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active.is_(True),
            )
        )
        if plan is None:
            raise AppError("plan_not_found", "Программа не найдена", status_code=404)
        return plan

    @staticmethod
    async def list_admin(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[SubscriptionPlan], int]:
        items = list(
            (
                await session.scalars(
                    select(SubscriptionPlan)
                    .order_by(TIER_ORDER, SubscriptionPlan.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(await session.scalar(select(func.count()).select_from(SubscriptionPlan)) or 0)
        return items, total

    @staticmethod
    async def get_admin(session: AsyncSession, plan_id: UUID) -> SubscriptionPlan:
        plan = await session.get(SubscriptionPlan, plan_id)
        if plan is None:
            raise AppError("plan_not_found", "Программа не найдена", status_code=404)
        return plan

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        data: PlanCreate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> SubscriptionPlan:
        plan = SubscriptionPlan(
            title=data.title,
            tier=data.tier,
            short_description=data.short_description,
            full_description=data.full_description,
            image_url=data.image_url,
            price_atomic=parse_amount(data.price),
            access_duration_value=data.access_duration_value,
            access_duration_unit=data.access_duration_unit,
            reward_amount_atomic=parse_amount(data.reward_amount),
            reward_frequency=data.reward_frequency,
            reward_duration_value=data.reward_duration_value,
            reward_duration_unit=data.reward_duration_unit,
            is_active=data.is_active,
        )
        session.add(plan)
        await session.flush()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="plan_created",
            entity_type="subscription_plan",
            entity_id=plan.id,
            new_data=plan_snapshot(plan),
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(plan)
        return plan

    @staticmethod
    async def update(
        session: AsyncSession,
        *,
        plan_id: UUID,
        data: PlanUpdate,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> SubscriptionPlan:
        plan = await session.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id).with_for_update(of=SubscriptionPlan)
        )
        if plan is None:
            raise AppError("plan_not_found", "Программа не найдена", status_code=404)
        old_data = plan_snapshot(plan)
        changes = data.model_dump(exclude_unset=True)
        if "price" in changes:
            plan.price_atomic = parse_amount(changes.pop("price"))
        if "reward_amount" in changes:
            plan.reward_amount_atomic = parse_amount(changes.pop("reward_amount"))
        for field, value in changes.items():
            setattr(plan, field, value)
        await session.flush()
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="plan_updated",
            entity_type="subscription_plan",
            entity_id=plan.id,
            old_data=old_data,
            new_data=plan_snapshot(plan),
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(plan)
        return plan

    @staticmethod
    async def set_active(
        session: AsyncSession,
        *,
        plan_id: UUID,
        is_active: bool,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> SubscriptionPlan:
        plan = await session.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id).with_for_update(of=SubscriptionPlan)
        )
        if plan is None:
            raise AppError("plan_not_found", "Программа не найдена", status_code=404)
        old_data = plan_snapshot(plan)
        plan.is_active = is_active
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="plan_activated" if is_active else "plan_deactivated",
            entity_type="subscription_plan",
            entity_id=plan.id,
            old_data=old_data,
            new_data=plan_snapshot(plan),
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(plan)
        return plan
