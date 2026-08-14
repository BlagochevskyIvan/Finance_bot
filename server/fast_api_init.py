from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram import Update
from telegram.ext import Application

from config.envcfg import (
    BOT_ENABLED,
    DROP_PENDING,
    TELEGRAM_SECRET,
    WEBHOOK_PATH,
    WEBHOOK_URL,
)
from config.logger import logger
from handlers.bot_init import BOT_COMMANDS, create_bot_app
from server.routers.api_router import router as api_router
from server.routers.common_router import router as common_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_app: Application | None = None

    if BOT_ENABLED:
        bot_app = create_bot_app()
        app.state.bot_app = bot_app
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.bot.set_my_commands(BOT_COMMANDS)
        await bot_app.bot.set_webhook(
            url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=DROP_PENDING,
            secret_token=TELEGRAM_SECRET or None,
        )
        logger.info(
            "Telegram commands and webhook set: %s%s", WEBHOOK_URL, WEBHOOK_PATH
        )
    else:
        logger.info("Telegram bot is disabled; set BOT_ENABLED=true to start it")

    yield

    if bot_app is not None:
        try:
            await bot_app.bot.delete_webhook()
        finally:
            await bot_app.stop()
            await bot_app.shutdown()
            logger.info("Telegram webhook deleted and bot stopped")


def init_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Base Telegram Bot API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(common_router)
    app.include_router(api_router, prefix="/api")
    return app
