# Исправление сохранения авторизации

Сессия пользователя и администратора теперь сохраняется после обновления или повторного открытия сайта на том же домене.

Изменены файлы:

- `customer-frontend/src/auth/tokenStore.ts`
- `customer-frontend/src/auth/AuthContext.tsx`
- `customer-frontend/src/api/client.ts`
- `admin-frontend/src/auth/tokenStore.ts`
- `admin-frontend/src/auth/AuthContext.tsx`
- `admin-frontend/src/api/client.ts`

Добавлены автоматические проверки:

- `customer-frontend/src/test/auth-persistence.test.tsx`
- `admin-frontend/src/test/auth-persistence.test.tsx`

После замены исходников необходимо пересобрать frontend-контейнеры или production build.
