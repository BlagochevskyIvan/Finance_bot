from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import escape

from sqlalchemy.exc import SQLAlchemyError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from config.logger import logger
from config.states import EXPENSE_AMOUNT, EXPENSE_CATEGORY, EXPENSE_DESCRIPTION
from db.database import AsyncSessionLocal
from db.repositories import add_expense, upsert_user
from handlers.common import main_menu_keyboard, show_main_menu, start


DRAFT_KEY = "expense_draft"
CATEGORIES = {
    "food": "🍔 Еда",
    "transport": "🚕 Транспорт",
    "home": "🏠 Дом",
    "health": "💊 Здоровье",
    "fun": "🎉 Развлечения",
    "other": "📦 Другое",
}


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Отмена", callback_data="expense:cancel")]]
    )


def category_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(label, callback_data=f"expense:category:{key}")
        for key, label in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(
        [buttons[index : index + 2] for index in range(0, len(buttons), 2)]
        + [[InlineKeyboardButton("Отмена", callback_data="expense:cancel")]]
    )


async def start_add_expense(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    context.user_data[DRAFT_KEY] = {}
    prompt = "Введите сумму расхода в рублях, например: <code>1250,50</code>"

    if query is not None:
        await query.answer()
        await query.edit_message_text(
            prompt,
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_keyboard(),
        )
    elif update.effective_message is not None:
        await update.effective_message.reply_text(
            prompt,
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_keyboard(),
        )
    else:
        context.user_data.pop(DRAFT_KEY, None)
        return ConversationHandler.END

    return EXPENSE_AMOUNT


def parse_amount(raw_value: str) -> Decimal | None:
    normalized = "".join(raw_value.split()).replace(",", ".")
    try:
        amount = Decimal(normalized).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None

    if (
        not amount.is_finite()
        or amount <= 0
        or amount > Decimal("9999999999.99")
    ):
        return None
    return amount


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.effective_message
    if message is None or message.text is None:
        return EXPENSE_AMOUNT

    amount = parse_amount(message.text)
    if amount is None:
        await message.reply_text(
            "Не удалось распознать сумму. Введите положительное число, например 350 или 1250,50.",
            reply_markup=cancel_keyboard(),
        )
        return EXPENSE_AMOUNT

    context.user_data.setdefault(DRAFT_KEY, {})["amount"] = str(amount)
    await message.reply_text("Выберите категорию:", reply_markup=category_keyboard())
    return EXPENSE_CATEGORY


async def receive_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is None or query.data is None:
        return EXPENSE_CATEGORY

    await query.answer()
    category_key = query.data.rsplit(":", maxsplit=1)[-1]
    category = CATEGORIES.get(category_key)
    if category is None:
        await query.edit_message_text(
            "Категория не найдена. Выберите категорию ещё раз:",
            reply_markup=category_keyboard(),
        )
        return EXPENSE_CATEGORY

    context.user_data.setdefault(DRAFT_KEY, {})["category"] = category
    await query.edit_message_text(
        "Добавьте комментарий к расходу или нажмите «Пропустить»:",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Пропустить", callback_data="expense:skip")],
                [InlineKeyboardButton("Отмена", callback_data="expense:cancel")],
            ]
        ),
    )
    return EXPENSE_DESCRIPTION


async def receive_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    message = update.effective_message
    if message is None or message.text is None:
        return EXPENSE_DESCRIPTION

    description = message.text.strip()
    if len(description) > 500:
        await message.reply_text(
            "Комментарий слишком длинный. Используйте не более 500 символов.",
            reply_markup=cancel_keyboard(),
        )
        return EXPENSE_DESCRIPTION

    return await save_expense(update, context, description=description or None)


async def skip_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query is not None:
        await query.answer()
    return await save_expense(update, context, description=None)


async def save_expense(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    description: str | None,
) -> int:
    telegram_user = update.effective_user
    draft = context.user_data.get(DRAFT_KEY, {})
    amount_raw = draft.get("amount")
    category = draft.get("category")

    if telegram_user is None or amount_raw is None or category is None:
        context.user_data.pop(DRAFT_KEY, None)
        await _send_result(
            update,
            "Данные расхода потерялись. Начните добавление заново.",
        )
        return ConversationHandler.END

    amount = Decimal(amount_raw)
    try:
        async with AsyncSessionLocal() as session:
            user = await upsert_user(session, telegram_user)
            await add_expense(
                session,
                user=user,
                amount=amount,
                category=category,
                description=description,
            )
            await session.commit()
    except SQLAlchemyError:
        logger.exception("Failed to add expense for Telegram user %s", telegram_user.id)
        await _send_result(
            update,
            "Не удалось сохранить расход. Попробуйте ещё раз позже.",
        )
        return ConversationHandler.END
    finally:
        context.user_data.pop(DRAFT_KEY, None)

    description_line = (
        f"\nКомментарий: {escape(description)}" if description else ""
    )
    await _send_result(
        update,
        "✅ <b>Расход сохранён</b>\n"
        f"Сумма: <b>{amount:.2f} RUB</b>\n"
        f"Категория: {escape(category)}"
        f"{description_line}",
    )
    return ConversationHandler.END


async def _send_result(update: Update, text: str) -> None:
    query = update.callback_query
    if query is not None and query.message is not None:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )
        return

    message = update.effective_message
    if message is not None:
        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=main_menu_keyboard(),
        )


async def cancel_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop(DRAFT_KEY, None)
    query = update.callback_query
    if query is not None:
        await query.answer()
    await _send_result(update, "Добавление расхода отменено.")
    return ConversationHandler.END


async def restart_from_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.pop(DRAFT_KEY, None)
    await start(update, context)
    return ConversationHandler.END


async def menu_from_conversation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.pop(DRAFT_KEY, None)
    await show_main_menu(update, context)
    return ConversationHandler.END
