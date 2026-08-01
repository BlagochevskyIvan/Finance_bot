from telegram.ext import Application, CommandHandler, PicklePersistence

from config.envcfg import BOT_CACHE_PATH, TELEGRAM_TOKEN
from config.logger import logger
from handlers.common import start


def create_bot_app() -> Application:
    BOT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    persistence = PicklePersistence(filepath=BOT_CACHE_PATH)
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .persistence(persistence)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    logger.info("Telegram bot application initialized")
    return application
