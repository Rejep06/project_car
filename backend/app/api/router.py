"""Сборка всех маршрутов версии API."""

from fastapi import APIRouter

from app.api.routes import auth, plans, posts, subscriptions, support, system, users, wallet
from app.api.routes.admin import (
    audit as admin_audit,
    deposits as admin_deposits,
    plans as admin_plans,
    posts as admin_posts,
    support as admin_support,
    users as admin_users,
    withdrawals as admin_withdrawals,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(plans.router)
api_router.include_router(subscriptions.router)
api_router.include_router(wallet.router)
api_router.include_router(posts.router)
api_router.include_router(support.router)
api_router.include_router(admin_plans.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_deposits.router)
api_router.include_router(admin_withdrawals.router)
api_router.include_router(admin_posts.router)
api_router.include_router(admin_support.router)
api_router.include_router(admin_audit.router)
