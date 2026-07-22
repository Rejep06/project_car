# Итоговое дерево backend-проекта

```text
subscription_platform_backend/
├── alembic/
│   ├── versions/
│   │   ├── 0001_initial.py
│   │   └── 0002_add_late_deposit_flag.py
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit.py
│   │   │   │   ├── deposits.py
│   │   │   │   ├── plans.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── support.py
│   │   │   │   ├── users.py
│   │   │   │   └── withdrawals.py
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── plans.py
│   │   │   ├── posts.py
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
│   │   ├── binance/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── schemas.py
│   │   │   └── signature.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── common.py
│   │   ├── deposit.py
│   │   ├── plan.py
│   │   ├── post.py
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
│   │   ├── plan_service.py
│   │   ├── post_service.py
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
│   │   └── pagination.py
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── deposit_worker.py
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
│   ├── test_binance_client.py
│   ├── test_deposits.py
│   ├── test_frontend_integration.py
│   ├── test_posts_money_files.py
│   ├── test_subscriptions_and_rewards.py
│   ├── test_support.py
│   └── test_withdrawals.py
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
