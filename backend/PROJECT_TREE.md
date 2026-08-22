# Дерево backend

```text
backend/
├── alembic/
│   ├── versions/
│   │   ├── 0001_initial.py
│   │   ├── 0002_add_late_deposit_flag.py
│   │   ├── 0003_business_logic.py
│   │   ├── 0004_infura_erc20.py
│   │   ├── 0005_email_lottery.py
│   │   └── 0006_legal_consent_evidence.py
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit.py
│   │   │   │   ├── deposit_wallets.py
│   │   │   │   ├── deposits.py
│   │   │   │   ├── lotteries.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── support.py
│   │   │   │   ├── users.py
│   │   │   │   └── withdrawals.py
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── lotteries.py
│   │   │   ├── notifications.py
│   │   │   ├── plans.py
│   │   │   ├── posts.py
│   │   │   ├── referrals.py
│   │   │   ├── subscriptions.py
│   │   │   ├── support.py
│   │   │   ├── system.py
│   │   │   ├── users.py
│   │   │   └── wallet.py
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py
│   │   │   ├── auth_session.py
│   │   │   ├── deposit.py
│   │   │   ├── deposit_wallet.py
│   │   │   ├── email_auth.py
│   │   │   ├── lottery.py
│   │   │   ├── notification.py
│   │   │   ├── post.py
│   │   │   ├── reward.py
│   │   │   ├── subscription.py
│   │   │   ├── support.py
│   │   │   ├── user.py
│   │   │   ├── wallet.py
│   │   │   └── withdrawal.py
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── enums.py
│   │   └── session.py
│   ├── integrations/
│   │   ├── infura/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   └── schemas.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── deposit.py
│   │   ├── deposit_wallet.py
│   │   ├── lottery.py
│   │   ├── notification.py
│   │   ├── plan.py
│   │   ├── post.py
│   │   ├── referral.py
│   │   ├── subscription.py
│   │   ├── support.py
│   │   ├── system.py
│   │   ├── user.py
│   │   ├── wallet.py
│   │   └── withdrawal.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audit_service.py
│   │   ├── auth_service.py
│   │   ├── deposit_service.py
│   │   ├── deposit_wallet_service.py
│   │   ├── email_service.py
│   │   ├── legal_service.py
│   │   ├── lottery_service.py
│   │   ├── notification_service.py
│   │   ├── plan_service.py
│   │   ├── post_service.py
│   │   ├── referral_service.py
│   │   ├── reward_service.py
│   │   ├── subscription_service.py
│   │   ├── support_service.py
│   │   ├── user_service.py
│   │   ├── wallet_service.py
│   │   └── withdrawal_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── datetime.py
│   │   ├── files.py
│   │   ├── money.py
│   │   ├── pagination.py
│   │   └── slug.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── deposit_worker.py
│   │   ├── email_worker.py
│   │   └── reward_worker.py
│   ├── __init__.py
│   └── main.py
├── scripts/
│   ├── __init__.py
│   ├── create_admin.py
│   └── seed_demo_data.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fakes.py
│   ├── test_auth_and_access.py
│   ├── test_business_logic.py
│   ├── test_deposits.py
│   ├── test_email_lottery.py
│   ├── test_email_worker.py
│   ├── test_frontend_integration.py
│   ├── test_infura_client.py
│   ├── test_locking_regressions.py
│   ├── test_posts_money_files.py
│   ├── test_subscriptions_and_rewards.py
│   ├── test_support.py
│   └── test_withdrawals.py
├── uploads/
│   ├── support/
│   │   └── .gitkeep
│   └── .gitkeep
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── PROJECT_TREE.md
├── pytest.ini
├── README.md
└── requirements.txt
```
