# Base for Telegram bots

Универсальный каркас Telegram-бота с одностраничным Mini App

- Telegram-бот на `python-telegram-bot`: команда `/start` показывает главную
  страницу с кнопкой **«Открыть Mini App»**.
- FastAPI: Telegram webhook, healthcheck, Swagger и API Mini App.
- Проверка подписи Telegram `initData` на backend.
- PostgreSQL и асинхронный SQLAlchemy.
- Alembic с начальной миграцией таблицы `users`.
- Одностраничный Mini App на Next.js.
- nginx как единая точка входа: frontend, `/api/*`, `/telegram`, `/docs`.
- Docker Compose для запуска всего стека.