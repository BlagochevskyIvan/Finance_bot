from fastapi import Header, HTTPException

from server.auth.telegram import TelegramUser, validate_init_data


async def get_current_telegram_user(
    x_telegram_auth: str | None = Header(default=None, alias="X-Telegram-Auth"),
) -> TelegramUser:
    if not x_telegram_auth:
        raise HTTPException(status_code=401, detail="X-Telegram-Auth header is missing")
    return validate_init_data(x_telegram_auth)
