# Дерево admin frontend

```text
admin-frontend/
├── public/
│   ├── assets/
│   │   ├── favicon.png
│   │   ├── hero-car-photo.jpg
│   │   ├── logo.png
│   │   └── program-car-photo.jpg
│   ├── README.md
│   └── robots.txt
├── src/
│   ├── api/
│   │   ├── audit.ts
│   │   ├── auth.ts
│   │   ├── client.ts
│   │   ├── deposits.ts
│   │   ├── depositWallets.ts
│   │   ├── plans.ts
│   │   ├── posts.ts
│   │   ├── support.ts
│   │   ├── types.ts
│   │   ├── users.ts
│   │   └── withdrawals.ts
│   ├── auth/
│   │   ├── AdminRoute.tsx
│   │   ├── AuthContext.tsx
│   │   └── tokenStore.ts
│   ├── components/
│   │   ├── AdminLayout.tsx
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── DataTable.tsx
│   │   ├── EmptyState.tsx
│   │   ├── FormField.tsx
│   │   ├── LoadingSpinner.tsx
│   │   ├── Modal.tsx
│   │   ├── PageHeader.tsx
│   │   ├── Pagination.tsx
│   │   ├── StatusBadge.tsx
│   │   └── Toast.tsx
│   ├── config/
│   │   └── assets.ts
│   ├── pages/
│   │   ├── AuditPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── DepositDetailsPage.tsx
│   │   ├── DepositsPage.tsx
│   │   ├── DepositWalletsPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── NotFoundPage.tsx
│   │   ├── PlanFormPage.tsx
│   │   ├── PlansPage.tsx
│   │   ├── PostFormPage.tsx
│   │   ├── PostsPage.tsx
│   │   ├── SupportDetailsPage.tsx
│   │   ├── SupportPage.tsx
│   │   ├── UserDetailsPage.tsx
│   │   ├── UsersPage.tsx
│   │   ├── WithdrawalDetailsPage.tsx
│   │   └── WithdrawalsPage.tsx
│   ├── styles/
│   │   ├── admin.css
│   │   ├── base.css
│   │   └── responsive.css
│   ├── test/
│   │   ├── auth-persistence.test.tsx
│   │   ├── auth-plans.test.tsx
│   │   ├── fixtures.ts
│   │   ├── helpers.tsx
│   │   ├── operations.test.tsx
│   │   └── setup.ts
│   ├── utils/
│   │   ├── date.ts
│   │   ├── labels.ts
│   │   └── money.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .dockerignore
├── .env.example
├── .gitignore
├── BACKEND_API_MAP.md
├── Dockerfile
├── eslint.config.js
├── index.html
├── nginx.conf
├── package-lock.json
├── package.json
├── PROJECT_TREE.md
├── README.md
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
├── VALIDATION_REPORT.md
└── vite.config.ts
```
