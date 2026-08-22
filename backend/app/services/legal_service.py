"""Фиксация юридически значимых согласий пользователя."""

from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.enums import LegalDocumentType
from app.db.models import LegalConsent


CONTRACT_ACCEPTANCE_TEXT = (
    "Я принимаю Пользовательское соглашение и Правила клиентских программ "
    "и лотерей, включая условия оплаты, начислений, возвратов, участия в "
    "розыгрышах и получения призов."
)

PRIVACY_ACCEPTANCE_TEXT = (
    "Я ознакомился с Политикой конфиденциальности и даю согласие на "
    "обработку персональных данных на условиях отдельного Согласия."
)

ELIGIBILITY_ACCEPTANCE_TEXT = (
    "Я подтверждаю, что мне исполнилось 18 лет, я полностью дееспособен, "
    "действую от своего имени, предоставляю достоверные сведения и вправе "
    "пользоваться сервисом по применимому законодательству."
)


class LegalService:
    @staticmethod
    async def record_registration_consents(
        session: AsyncSession,
        *,
        user_id: UUID,
        account_email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> list[LegalConsent]:
        """Записывает пять документов, принятых тремя видимыми чекбоксами.

        У каждого документа остаётся собственная версия. Одновременно
        сохраняются единый batch-id, точная формулировка чекбокса, URL документа,
        email на момент акцепта, IP и User-Agent. Это позволяет восстановить,
        какие именно документы и каким действием принял пользователь.
        """

        settings = get_settings()
        batch_id = uuid4()
        base_url = settings.frontend_base_url
        normalized_email = account_email.strip().lower()
        documents = [
            (
                LegalDocumentType.TERMS_OF_USE,
                settings.terms_version,
                "contract",
                f"{base_url}/terms",
                CONTRACT_ACCEPTANCE_TEXT,
            ),
            (
                LegalDocumentType.PROGRAM_RULES,
                settings.program_rules_version,
                "contract",
                f"{base_url}/program-rules",
                CONTRACT_ACCEPTANCE_TEXT,
            ),
            (
                LegalDocumentType.PRIVACY_POLICY,
                settings.privacy_policy_version,
                "privacy",
                f"{base_url}/privacy",
                PRIVACY_ACCEPTANCE_TEXT,
            ),
            (
                LegalDocumentType.PERSONAL_DATA_PROCESSING,
                settings.personal_data_processing_version,
                "privacy",
                f"{base_url}/personal-data-consent",
                PRIVACY_ACCEPTANCE_TEXT,
            ),
            (
                LegalDocumentType.AGE_CONFIRMATION,
                settings.age_confirmation_version,
                "eligibility",
                f"{base_url}/terms#eligibility",
                ELIGIBILITY_ACCEPTANCE_TEXT,
            ),
        ]
        items = [
            LegalConsent(
                user_id=user_id,
                document_type=document_type,
                document_version=version,
                acceptance_batch_id=batch_id,
                acceptance_form_version=settings.registration_consent_form_version,
                consent_group=consent_group,
                account_email=normalized_email,
                document_url=document_url,
                acceptance_text=acceptance_text,
                ip_address=ip_address,
                user_agent=(user_agent or "")[:500] or None,
            )
            for (
                document_type,
                version,
                consent_group,
                document_url,
                acceptance_text,
            ) in documents
        ]
        session.add_all(items)
        await session.flush()
        return items
