"""REST-маршруты регистрации и JWT-сессий."""

from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Авторизация"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, session: SessionDep) -> UserRead:
    user = await AuthService.register(session, email=str(data.email), password=data.password)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPairResponse)
async def login(data: LoginRequest, session: SessionDep) -> TokenPairResponse:
    return await AuthService.login(session, email=str(data.email), password=data.password)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(data: RefreshRequest, session: SessionDep) -> TokenPairResponse:
    return await AuthService.refresh(session, data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(data: LogoutRequest, session: SessionDep) -> MessageResponse:
    await AuthService.logout(session, data.refresh_token)
    return MessageResponse(message="Сессия завершена")
