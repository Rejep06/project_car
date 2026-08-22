# Дерево проекта

```text
/
├── admin-frontend/
│   ├── public/
│   │   ├── assets/
│   │   │   ├── favicon.png
│   │   │   ├── hero-car-photo.jpg
│   │   │   ├── logo.png
│   │   │   └── program-car-photo.jpg
│   │   ├── README.md
│   │   └── robots.txt
│   ├── src/
│   │   ├── api/
│   │   │   ├── audit.ts
│   │   │   ├── auth.ts
│   │   │   ├── client.ts
│   │   │   ├── deposits.ts
│   │   │   ├── depositWallets.ts
│   │   │   ├── lotteries.ts
│   │   │   ├── plans.ts
│   │   │   ├── posts.ts
│   │   │   ├── support.ts
│   │   │   ├── types.ts
│   │   │   ├── users.ts
│   │   │   └── withdrawals.ts
│   │   ├── auth/
│   │   │   ├── AdminRoute.tsx
│   │   │   ├── AuthContext.tsx
│   │   │   └── tokenStore.ts
│   │   ├── components/
│   │   │   ├── AdminLayout.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── FormField.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── LotteryCard.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── Toast.tsx
│   │   ├── config/
│   │   │   └── assets.ts
│   │   ├── pages/
│   │   │   ├── AuditPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── DepositDetailsPage.tsx
│   │   │   ├── DepositsPage.tsx
│   │   │   ├── DepositWalletsPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── LotteriesPage.tsx
│   │   │   ├── LotteryFormPage.tsx
│   │   │   ├── NotFoundPage.tsx
│   │   │   ├── PlanFormPage.tsx
│   │   │   ├── PlansPage.tsx
│   │   │   ├── PostFormPage.tsx
│   │   │   ├── PostsPage.tsx
│   │   │   ├── SupportDetailsPage.tsx
│   │   │   ├── SupportPage.tsx
│   │   │   ├── UserDetailsPage.tsx
│   │   │   ├── UsersPage.tsx
│   │   │   ├── WithdrawalDetailsPage.tsx
│   │   │   └── WithdrawalsPage.tsx
│   │   ├── styles/
│   │   │   ├── admin.css
│   │   │   ├── base.css
│   │   │   └── responsive.css
│   │   ├── test/
│   │   │   ├── auth-persistence.test.tsx
│   │   │   ├── auth-plans.test.tsx
│   │   │   ├── fixtures.ts
│   │   │   ├── helpers.tsx
│   │   │   ├── operations.test.tsx
│   │   │   └── setup.ts
│   │   ├── utils/
│   │   │   ├── date.ts
│   │   │   ├── labels.ts
│   │   │   └── money.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .dockerignore
│   ├── .env.example
│   ├── .gitignore
│   ├── BACKEND_API_MAP.md
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   ├── PROJECT_TREE.md
│   ├── README.md
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── VALIDATION_REPORT.md
│   └── vite.config.ts
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   ├── 0001_initial.py
│   │   │   ├── 0002_add_late_deposit_flag.py
│   │   │   ├── 0003_business_logic.py
│   │   │   ├── 0004_infura_erc20.py
│   │   │   ├── 0005_email_lottery.py
│   │   │   └── 0006_legal_consent_evidence.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── admin/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── lotteries.py
│   │   │   │   ├── notifications.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── referrals.py
│   │   │   │   ├── subscriptions.py
│   │   │   │   ├── support.py
│   │   │   │   ├── system.py
│   │   │   │   ├── users.py
│   │   │   │   └── wallet.py
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit.py
│   │   │   │   ├── auth_session.py
│   │   │   │   ├── deposit.py
│   │   │   │   ├── deposit_wallet.py
│   │   │   │   ├── email_auth.py
│   │   │   │   ├── lottery.py
│   │   │   │   ├── notification.py
│   │   │   │   ├── post.py
│   │   │   │   ├── reward.py
│   │   │   │   ├── subscription.py
│   │   │   │   ├── support.py
│   │   │   │   ├── user.py
│   │   │   │   ├── wallet.py
│   │   │   │   └── withdrawal.py
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── enums.py
│   │   │   └── session.py
│   │   ├── integrations/
│   │   │   ├── infura/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py
│   │   │   │   └── schemas.py
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── auth.py
│   │   │   ├── common.py
│   │   │   ├── deposit.py
│   │   │   ├── deposit_wallet.py
│   │   │   ├── lottery.py
│   │   │   ├── notification.py
│   │   │   ├── plan.py
│   │   │   ├── post.py
│   │   │   ├── referral.py
│   │   │   ├── subscription.py
│   │   │   ├── support.py
│   │   │   ├── system.py
│   │   │   ├── user.py
│   │   │   ├── wallet.py
│   │   │   └── withdrawal.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── audit_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── deposit_service.py
│   │   │   ├── deposit_wallet_service.py
│   │   │   ├── email_service.py
│   │   │   ├── legal_service.py
│   │   │   ├── lottery_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── post_service.py
│   │   │   ├── referral_service.py
│   │   │   ├── reward_service.py
│   │   │   ├── subscription_service.py
│   │   │   ├── support_service.py
│   │   │   ├── user_service.py
│   │   │   ├── wallet_service.py
│   │   │   └── withdrawal_service.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── datetime.py
│   │   │   ├── files.py
│   │   │   ├── money.py
│   │   │   ├── pagination.py
│   │   │   └── slug.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── deposit_worker.py
│   │   │   ├── email_worker.py
│   │   │   └── reward_worker.py
│   │   ├── __init__.py
│   │   └── main.py
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── create_admin.py
│   │   ├── requeue_failed_emails.py
│   │   └── seed_demo_data.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── fakes.py
│   │   ├── test_auth_and_access.py
│   │   ├── test_business_logic.py
│   │   ├── test_deposits.py
│   │   ├── test_email_dns.py
│   │   ├── test_email_lottery.py
│   │   ├── test_email_worker.py
│   │   ├── test_frontend_integration.py
│   │   ├── test_infura_client.py
│   │   ├── test_locking_regressions.py
│   │   ├── test_posts_money_files.py
│   │   ├── test_subscriptions_and_rewards.py
│   │   ├── test_support.py
│   │   └── test_withdrawals.py
│   ├── uploads/
│   │   ├── support/
│   │   │   └── .gitkeep
│   │   └── .gitkeep
│   ├── .dockerignore
│   ├── .env.example
│   ├── .gitignore
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── PROJECT_TREE.md
│   ├── pytest.ini
│   ├── README.md
│   └── requirements.txt
├── customer-frontend/
│   ├── public/
│   │   ├── assets/
│   │   │   ├── favicon.png
│   │   │   ├── hero-car-photo.jpg
│   │   │   ├── logo.png
│   │   │   └── program-car-photo.jpg
│   │   ├── README.md
│   │   └── robots.txt
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.ts
│   │   │   ├── client.ts
│   │   │   ├── lotteries.ts
│   │   │   ├── notifications.ts
│   │   │   ├── plans.ts
│   │   │   ├── posts.ts
│   │   │   ├── referrals.ts
│   │   │   ├── subscriptions.ts
│   │   │   ├── support.ts
│   │   │   ├── system.ts
│   │   │   ├── types.ts
│   │   │   ├── users.ts
│   │   │   └── wallet.ts
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── tokenStore.ts
│   │   ├── components/
│   │   │   ├── AccountLayout.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   ├── CopyButton.tsx
│   │   │   ├── DepositStatusPanel.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── LotteryCard.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── MoneyValue.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── PlanCard.tsx
│   │   │   ├── ProgramImage.tsx
│   │   │   ├── PublicLayout.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── Toast.tsx
│   │   ├── config/
│   │   │   ├── assets.ts
│   │   │   └── content.ts
│   │   ├── pages/
│   │   │   ├── account/
│   │   │   │   ├── AccountDashboardPage.tsx
│   │   │   │   ├── AccountLotteriesPage.tsx
│   │   │   │   ├── DepositDetailsPage.tsx
│   │   │   │   ├── DepositsPage.tsx
│   │   │   │   ├── NotificationsPage.tsx
│   │   │   │   ├── ProfilePage.tsx
│   │   │   │   ├── ReferralsPage.tsx
│   │   │   │   ├── RewardsPage.tsx
│   │   │   │   ├── SubscriptionDetailsPage.tsx
│   │   │   │   ├── SubscriptionsPage.tsx
│   │   │   │   ├── SupportDetailsPage.tsx
│   │   │   │   ├── SupportPage.tsx
│   │   │   │   ├── TransactionsPage.tsx
│   │   │   │   ├── WalletPage.tsx
│   │   │   │   └── WithdrawalsPage.tsx
│   │   │   ├── AboutPage.tsx
│   │   │   ├── CheckEmailPage.tsx
│   │   │   ├── FaqPage.tsx
│   │   │   ├── ForgotPasswordPage.tsx
│   │   │   ├── HomePage.tsx
│   │   │   ├── HowItWorksPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── LotteriesPage.tsx
│   │   │   ├── LotteryDetailsPage.tsx
│   │   │   ├── NewsDetailsPage.tsx
│   │   │   ├── NewsPage.tsx
│   │   │   ├── NotFoundPage.tsx
│   │   │   ├── PersonalDataConsentPage.tsx
│   │   │   ├── PlanDetailsPage.tsx
│   │   │   ├── PlansPage.tsx
│   │   │   ├── PrivacyPage.tsx
│   │   │   ├── ProgramRulesPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── ResetPasswordPage.tsx
│   │   │   ├── TermsPage.tsx
│   │   │   └── VerifyEmailPage.tsx
│   │   ├── styles/
│   │   │   ├── base.css
│   │   │   ├── components.css
│   │   │   ├── pages.css
│   │   │   └── responsive.css
│   │   ├── test/
│   │   │   ├── auth-persistence.test.tsx
│   │   │   ├── customer.test.tsx
│   │   │   ├── deposits-support-withdrawals.test.tsx
│   │   │   ├── fixtures.ts
│   │   │   ├── registration-consents.test.tsx
│   │   │   ├── render.tsx
│   │   │   └── setup.ts
│   │   ├── utils/
│   │   │   ├── date.ts
│   │   │   ├── money.ts
│   │   │   ├── programs.ts
│   │   │   └── rewards.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .dockerignore
│   ├── .env.example
│   ├── .gitignore
│   ├── BACKEND_API_MAP.md
│   ├── Dockerfile
│   ├── eslint.config.js
│   ├── index.html
│   ├── nginx.conf
│   ├── package-lock.json
│   ├── package.json
│   ├── PROJECT_TREE.md
│   ├── README.md
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── VALIDATION_REPORT.md
│   └── vite.config.ts
├── .env.example
├── .gitignore
├── ASSET_SOURCES.md
├── BACKEND_API_MAP.md
├── BACKEND_CHANGES.md
├── BACKEND_OPENAPI.json
├── BUSINESS_LOGIC_UPDATE.md
├── COMPOSE_ENVIRONMENTS.md
├── DEPLOY_DNS_LOTTERY_FIX.md
├── docker-compose.server.example.yml
├── docker-compose.yml
├── EMAIL_LOTTERY_CHANGES.md
├── EMAIL_SETUP.md
├── FIX_MANIFEST_2026-08-22.md
├── INFURA_SETUP.md
├── LOTTERY_SETUP.md
├── LEGAL_CONSENT_UPDATE.md
├── PROJECT_TREE.md
├── README.md
├── SESSION_PERSISTENCE_FIX.md
├── UPGRADE_EMAIL_LOTTERY.md
└── VALIDATION_REPORT.md
```
