"""Профиль текущего пользователя."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUserDep, SessionDep
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUserDep) -> UserRead:
    return UserRead.from_user(current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserRead:
    user = await UserService.update_me(
        session, user_id=current_user.id, email=str(data.email)
    )
    return UserRead.from_user(user)
