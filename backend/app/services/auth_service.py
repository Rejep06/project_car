"""Регистрация, подтверждение email, восстановление пароля и JWT-сессии."""

from __future__ import annotations

from datetime import timedelta
import hmac
import secrets
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_action_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.enums import EmailVerificationPurpose, UserRole
from app.db.models import (
    AuthSession,
    EmailVerificationToken,
    PasswordResetToken,
    User,
)
from app.schemas.auth import RegistrationResponse, TokenPairResponse
from app.services.email_service import EmailService
from app.services.legal_service import LegalService
from app.services.wallet_service import WalletService
from app.utils.datetime import ensure_utc, utcnow


class AuthService:
    @staticmethod
    async def _invalidate_email_tokens(
        session: AsyncSession,
        *,
        user_id: UUID,
        purpose: EmailVerificationPurpose,
    ) -> None:
        await session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.purpose == purpose,
                EmailVerificationToken.used_at.is_(None),
            )
            .values(used_at=utcnow())
        )

    @staticmethod
    async def _create_email_verification_token(
        session: AsyncSession,
        *,
        user: User,
        target_email: str,
        purpose: EmailVerificationPurpose,
    ) -> str:
        settings = get_settings()
        await AuthService._invalidate_email_tokens(
            session, user_id=user.id, purpose=purpose
        )
        raw_token = secrets.token_urlsafe(48)
        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_action_token(raw_token),
            purpose=purpose,
            target_email=target_email.strip().lower(),
            expires_at=utcnow()
            + timedelta(hours=settings.email_verification_ttl_hours),
        )
        session.add(token)
        await session.flush()
        await EmailService.queue_verification_email(
            session,
            recipient_email=target_email,
            token=raw_token,
            is_email_change=purpose == EmailVerificationPurpose.EMAIL_CHANGE,
        )
        return raw_token

    @staticmethod
    async def register(
        session: AsyncSession,
        *,
        email: str,
        password: str,
        referral_code: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RegistrationResponse:
        settings = get_settings()
        normalized_email = email.strip().lower()
        existing = await session.scalar(
            select(User.id).where(User.email == normalized_email)
        )
        if existing is not None:
            raise AppError(
                "email_already_exists",
                "Пользователь с таким email уже существует",
                status_code=409,
            )

        pending_owner = await session.scalar(
            select(User.id).where(User.pending_email == normalized_email)
        )
        if pending_owner is not None:
            raise AppError(
                "email_already_exists",
                "Этот email уже ожидает подтверждения в другом аккаунте",
                status_code=409,
            )

        referrer: User | None = None
        if referral_code:
            referrer = await session.scalar(
                select(User).where(
                    User.referral_code == referral_code.strip().upper(),
                    User.is_active.is_(True),
                )
            )
            if referrer is None:
                raise AppError(
                    "referral_code_not_found",
                    "Реферальная ссылка недействительна",
                    status_code=404,
                )

        user_id = uuid4()
        user = User(
            id=user_id,
            email=normalized_email,
            password_hash=hash_password(password),
            role=UserRole.USER,
            is_active=True,
            is_frozen=False,
            email_verified_at=None,
            referral_code=user_id.hex[:16].upper(),
            referred_by_user_id=referrer.id if referrer else None,
        )
        session.add(user)
        try:
            await session.flush()
            await WalletService.create_wallet(session, user.id)
            await LegalService.record_registration_consents(
                session,
                user_id=user.id,
                account_email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raw_token = await AuthService._create_email_verification_token(
                session,
                user=user,
                target_email=user.email,
                purpose=EmailVerificationPurpose.REGISTRATION,
            )
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError(
                "email_already_exists",
                "Пользователь с таким email уже существует",
                status_code=409,
            ) from exc

        return RegistrationResponse(
            email=user.email,
            message=(
                "Аккаунт создан. Мы отправили письмо со ссылкой для подтверждения email."
            ),
            debug_verification_token=(
                raw_token
                if settings.app_env != "production"
                and not settings.email_delivery_enabled
                else None
            ),
        )

    @staticmethod
    async def verify_email(session: AsyncSession, raw_token: str) -> str:
        token = await session.scalar(
            select(EmailVerificationToken)
            .where(EmailVerificationToken.token_hash == hash_action_token(raw_token))
            .with_for_update(of=EmailVerificationToken)
        )
        if token is None or token.used_at is not None:
            raise AppError(
                "invalid_email_verification_token",
                "Ссылка подтверждения недействительна или уже использована",
                status_code=400,
            )
        if ensure_utc(token.expires_at) <= utcnow():
            raise AppError(
                "email_verification_token_expired",
                "Срок действия ссылки истёк. Запросите новое письмо",
                status_code=400,
            )

        user = await session.scalar(
            select(User)
            .where(User.id == token.user_id)
            .with_for_update(of=User)
        )
        if user is None or not user.is_active:
            raise AppError("user_inactive", "Пользователь недоступен", status_code=403)

        target_email = token.target_email.strip().lower()
        if token.purpose == EmailVerificationPurpose.REGISTRATION:
            if target_email != user.email:
                raise AppError(
                    "email_verification_mismatch",
                    "Email в ссылке больше не соответствует аккаунту",
                    status_code=409,
                )
            user.email_verified_at = utcnow()
        else:
            existing = await session.scalar(
                select(User.id).where(
                    User.email == target_email,
                    User.id != user.id,
                )
            )
            if existing is not None:
                raise AppError(
                    "email_already_exists",
                    "Этот email уже используется",
                    status_code=409,
                )
            user.email = target_email
            user.pending_email = None
            user.email_verified_at = utcnow()
            await session.execute(
                update(AuthSession)
                .where(
                    AuthSession.user_id == user.id,
                    AuthSession.revoked_at.is_(None),
                )
                .values(revoked_at=utcnow())
            )

        token.used_at = utcnow()
        await session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.id != token.id,
                EmailVerificationToken.used_at.is_(None),
            )
            .values(used_at=utcnow())
        )
        await session.commit()
        return user.email

    @staticmethod
    async def resend_verification(session: AsyncSession, email: str) -> str | None:
        """Создаёт новое письмо, но не раскрывает существование аккаунта."""
        settings = get_settings()
        normalized_email = email.strip().lower()
        user = await session.scalar(
            select(User).where(
                User.email == normalized_email,
                User.is_active.is_(True),
            )
        )
        if user is None or user.email_verified_at is not None:
            return None

        latest = await session.scalar(
            select(func.max(EmailVerificationToken.created_at)).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.purpose
                == EmailVerificationPurpose.REGISTRATION,
            )
        )
        if latest is not None and (
            utcnow() - ensure_utc(latest)
        ).total_seconds() < settings.email_request_cooldown_seconds:
            return None

        raw_token = await AuthService._create_email_verification_token(
            session,
            user=user,
            target_email=user.email,
            purpose=EmailVerificationPurpose.REGISTRATION,
        )
        await session.commit()
        if settings.app_env != "production" and not settings.email_delivery_enabled:
            return raw_token
        return None

    @staticmethod
    async def request_email_change(
        session: AsyncSession,
        *,
        user_id: UUID,
        new_email: str,
    ) -> User:
        normalized = new_email.strip().lower()
        user = await session.scalar(
            select(User).where(User.id == user_id).with_for_update(of=User)
        )
        if user is None:
            raise AppError("user_not_found", "Пользователь не найден", status_code=404)
        if normalized == user.email:
            return user
        existing = await session.scalar(
            select(User.id).where(
                (User.email == normalized) | (User.pending_email == normalized),
                User.id != user.id,
            )
        )
        if existing is not None:
            raise AppError(
                "email_already_exists", "Этот email уже используется", status_code=409
            )
        user.pending_email = normalized
        await AuthService._create_email_verification_token(
            session,
            user=user,
            target_email=normalized,
            purpose=EmailVerificationPurpose.EMAIL_CHANGE,
        )
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def request_password_reset(session: AsyncSession, email: str) -> str | None:
        """Ставит письмо в очередь и всегда допускает одинаковый внешний ответ."""
        settings = get_settings()
        normalized_email = email.strip().lower()
        user = await session.scalar(
            select(User).where(
                User.email == normalized_email,
                User.is_active.is_(True),
            )
        )
        if user is None:
            return None

        latest = await session.scalar(
            select(func.max(PasswordResetToken.created_at)).where(
                PasswordResetToken.user_id == user.id
            )
        )
        if latest is not None and (
            utcnow() - ensure_utc(latest)
        ).total_seconds() < settings.email_request_cooldown_seconds:
            return None

        await session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=utcnow())
        )
        raw_token = secrets.token_urlsafe(48)
        session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_action_token(raw_token),
                expires_at=utcnow()
                + timedelta(minutes=settings.password_reset_ttl_minutes),
            )
        )
        await EmailService.queue_password_reset_email(
            session, recipient_email=user.email, token=raw_token
        )
        await session.commit()
        if settings.app_env != "production" and not settings.email_delivery_enabled:
            return raw_token
        return None

    @staticmethod
    async def reset_password(
        session: AsyncSession, *, raw_token: str, new_password: str
    ) -> str:
        token = await session.scalar(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == hash_action_token(raw_token))
            .with_for_update(of=PasswordResetToken)
        )
        if token is None or token.used_at is not None:
            raise AppError(
                "invalid_password_reset_token",
                "Ссылка восстановления недействительна или уже использована",
                status_code=400,
            )
        if ensure_utc(token.expires_at) <= utcnow():
            raise AppError(
                "password_reset_token_expired",
                "Срок действия ссылки истёк. Запросите новое письмо",
                status_code=400,
            )

        user = await session.scalar(
            select(User).where(User.id == token.user_id).with_for_update(of=User)
        )
        if user is None or not user.is_active:
            raise AppError("user_inactive", "Пользователь недоступен", status_code=403)

        user.password_hash = hash_password(new_password)
        if user.email_verified_at is None:
            user.email_verified_at = utcnow()
        token.used_at = utcnow()
        await session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.id != token.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=utcnow())
        )
        await session.execute(
            update(AuthSession)
            .where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=utcnow())
        )
        await EmailService.queue_password_changed_email(
            session, recipient_email=user.email
        )
        await session.commit()
        return user.email

    @staticmethod
    async def login(
        session: AsyncSession, *, email: str, password: str
    ) -> TokenPairResponse:
        normalized_email = email.strip().lower()
        user = await session.scalar(select(User).where(User.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            raise AppError(
                "invalid_credentials", "Неверный email или пароль", status_code=401
            )
        if not user.is_active:
            raise AppError(
                "user_inactive", "Пользователь деактивирован", status_code=403
            )
        if user.email_verified_at is None:
            raise AppError(
                "email_not_verified",
                "Подтвердите email по ссылке из письма",
                status_code=403,
                details={"email": user.email},
            )

        settings = get_settings()
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user.id,
            refresh_token_hash="pending",
            expires_at=utcnow()
            + timedelta(days=settings.refresh_token_expire_days),
        )
        refresh_token = create_refresh_token(user.id, auth_session.id)
        auth_session.refresh_token_hash = hash_refresh_token(refresh_token)
        session.add(auth_session)
        await session.commit()

        access_token, expires_in = create_access_token(user.id, user.role.value)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    async def refresh(session: AsyncSession, refresh_token: str) -> TokenPairResponse:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
        except (TokenValidationError, KeyError, ValueError) as exc:
            raise AppError(
                "invalid_refresh_token", "Недействительный refresh token", status_code=401
            ) from exc

        auth_session = await session.scalar(
            select(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
            .with_for_update(of=AuthSession)
        )
        if auth_session is None or auth_session.revoked_at is not None:
            raise AppError(
                "invalid_refresh_token", "Refresh token отозван", status_code=401
            )
        if ensure_utc(auth_session.expires_at) <= utcnow():
            raise AppError(
                "refresh_token_expired", "Refresh token истёк", status_code=401
            )
        candidate_hash = hash_refresh_token(refresh_token)
        if not hmac.compare_digest(auth_session.refresh_token_hash, candidate_hash):
            raise AppError(
                "invalid_refresh_token", "Недействительный refresh token", status_code=401
            )

        user = await session.get(User, user_id)
        if user is None or not user.is_active:
            raise AppError("user_inactive", "Пользователь недоступен", status_code=403)
        if user.email_verified_at is None:
            raise AppError(
                "email_not_verified", "Подтвердите email", status_code=403
            )

        new_refresh_token = create_refresh_token(user.id, auth_session.id)
        auth_session.refresh_token_hash = hash_refresh_token(new_refresh_token)
        await session.commit()
        access_token, expires_in = create_access_token(user.id, user.role.value)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    async def logout(session: AsyncSession, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
        except (TokenValidationError, KeyError, ValueError) as exc:
            raise AppError(
                "invalid_refresh_token", "Недействительный refresh token", status_code=401
            ) from exc

        auth_session = await session.scalar(
            select(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
            .with_for_update(of=AuthSession)
        )
        if auth_session is None:
            return
        if not hmac.compare_digest(
            auth_session.refresh_token_hash, hash_refresh_token(refresh_token)
        ):
            raise AppError(
                "invalid_refresh_token", "Недействительный refresh token", status_code=401
            )
        if auth_session.revoked_at is None:
            auth_session.revoked_at = utcnow()
            await session.commit()
