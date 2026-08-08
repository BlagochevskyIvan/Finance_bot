from html import escape

from sqlalchemy.exc import SQLAlchemyError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config.logger import logger
from db.database import AsyncSessionLocal
from db.repositories import get_recent_expenses, upsert_user


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Добавить расход", callback_data="expense:add")],
            [InlineKeyboardButton("📋 Последние расходы", callback_data="menu:recent")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="menu:help")],
        ]
    )


async def _send_or_edit(
    update: Update,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    query = update.callback_query
    if query is not None and query.message is not None:
        await query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
        return

    message = update.effective_message
    if message is not None:
        await message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    telegram_user = update.effective_user
    if telegram_user is None or update.effective_chat is None:
        return

    try:
        async with AsyncSessionLocal() as session:
            await upsert_user(session, telegram_user)
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Failed to save Telegram user %s", telegram_user.id)
        await _send_or_edit(update, "Не удалось подключиться к базе данных. Попробуйте позже.")
        return

    await _send_or_edit(
        update,
        f"Привет, {escape(telegram_user.first_name)}!\n\n"
        "Я помогу записывать расходы. Выберите действие:",
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML,
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.callback_query is not None:
        await update.callback_query.answer()
    await _send_or_edit(
        update,
        "Главное меню. Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


async def show_recent_expenses(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    del context
    query = update.callback_query
    telegram_user = update.effective_user
    if query is None or telegram_user is None:
        return
    await query.answer()

    try:
        async with AsyncSessionLocal() as session:
            user = await upsert_user(session, telegram_user)
            expenses = await get_recent_expenses(session, user.id)
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Failed to load expenses for Telegram user %s", telegram_user.id)
        await query.edit_message_text(
            "Не удалось загрузить расходы. Попробуйте позже.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if not expenses:
        text = "У вас пока нет расходов. Добавьте первый."
    else:
        rows = ["<b>Последние расходы:</b>"]
        for expense in expenses:
            description = (
                f" — {escape(expense.description)}" if expense.description else ""
            )
            rows.append(
                f"• {expense.spent_at:%d.%m.%Y} · "
                f"{escape(expense.category)} · "
                f"<b>{expense.amount:.2f} {escape(expense.currency)}</b>"
                f"{description}"
            )
        text = "\n".join(rows)

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ Добавить расход", callback_data="expense:add")],
                [InlineKeyboardButton("⬅️ В меню", callback_data="menu:main")],
            ]
        ),
    )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    query = update.callback_query
    if query is not None:
        await query.answer()
    await _send_or_edit(
        update,
        "<b>Как пользоваться ботом</b>\n\n"
        "1. Нажмите «Добавить расход».\n"
        "2. Введите сумму.\n"
        "3. Выберите категорию.\n"
        "4. Добавьте комментарий или пропустите этот шаг.\n\n"
        "Команда /cancel отменяет текущее добавление.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ В меню", callback_data="menu:main")]]
        ),
    )
