"""REST-маршруты регистрации, подтверждения email и JWT-сессий."""

from fastapi import APIRouter, Request, status

from app.api.dependencies import SessionDep
from app.schemas.auth import (
    EmailVerificationConfirmRequest,
    EmailVerificationResendRequest,
    EmailVerificationResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    RegistrationResponse,
    TokenPairResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Авторизация"])


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip() or None
    return request.client.host if request.client else None


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest, request: Request, session: SessionDep
) -> RegistrationResponse:
    return await AuthService.register(
        session,
        email=str(data.email),
        password=data.password,
        referral_code=data.referral_code,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/email-verification/confirm", response_model=EmailVerificationResponse
)
async def confirm_email(
    data: EmailVerificationConfirmRequest, session: SessionDep
) -> EmailVerificationResponse:
    email = await AuthService.verify_email(session, data.token)
    return EmailVerificationResponse(
        message="Email успешно подтверждён. Теперь можно войти в аккаунт.",
        email=email,
    )


@router.post(
    "/email-verification/resend", response_model=EmailVerificationResponse
)
async def resend_email_verification(
    data: EmailVerificationResendRequest, session: SessionDep
) -> EmailVerificationResponse:
    debug_token = await AuthService.resend_verification(session, str(data.email))
    message = (
        "Если аккаунт существует и email ещё не подтверждён, новое письмо уже отправлено."
    )
    if debug_token:
        message += f" Тестовый токен: {debug_token}"
    return EmailVerificationResponse(message=message)


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    data: PasswordResetRequest, session: SessionDep
) -> MessageResponse:
    debug_token = await AuthService.request_password_reset(session, str(data.email))
    message = "Если аккаунт существует, письмо для восстановления пароля отправлено."
    if debug_token:
        message += f" Тестовый токен: {debug_token}"
    return MessageResponse(message=message)


@router.post("/password-reset/confirm", response_model=EmailVerificationResponse)
async def confirm_password_reset(
    data: PasswordResetConfirmRequest, session: SessionDep
) -> EmailVerificationResponse:
    email = await AuthService.reset_password(
        session, raw_token=data.token, new_password=data.new_password
    )
    return EmailVerificationResponse(
        message="Пароль изменён. Все старые сессии завершены.", email=email
    )


@router.post("/login", response_model=TokenPairResponse)
async def login(data: LoginRequest, session: SessionDep) -> TokenPairResponse:
    return await AuthService.login(
        session, email=str(data.email), password=data.password
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(data: RefreshRequest, session: SessionDep) -> TokenPairResponse:
    return await AuthService.refresh(session, data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(data: LogoutRequest, session: SessionDep) -> MessageResponse:
    await AuthService.logout(session, data.refresh_token)
    return MessageResponse(message="Сессия завершена")
