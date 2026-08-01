from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import ContextTypes

from config.envcfg import WEBAPP_URL


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if chat is None:
        return

    name = user.first_name if user else "друг"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Открыть Mini App", web_app=WebAppInfo(url=WEBAPP_URL))]]
    )
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"Привет, {name}! Это главная страница бота.",
        reply_markup=keyboard,
    )
