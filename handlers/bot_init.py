from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

from config.envcfg import BOT_CACHE_PATH, TELEGRAM_TOKEN
from config.logger import logger
from config.states import EXPENSE_AMOUNT, EXPENSE_CATEGORY, EXPENSE_DESCRIPTION
from handlers.common import (
    confirm_delete_expense,
    show_help,
    show_main_menu,
    show_monthly_stats,
    show_recent_expenses,
    show_undo_expense,
    start,
)
from handlers.expenses import (
    cancel_expense,
    menu_from_conversation,
    receive_amount,
    receive_category,
    receive_description,
    restart_from_conversation,
    skip_description,
    start_add_expense,
)


def create_bot_app() -> Application:
    BOT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    persistence = PicklePersistence(filepath=BOT_CACHE_PATH)
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .persistence(persistence)
        .build()
    )
    expense_conversation = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_expense, pattern=r"^expense:add$")
        ],
        states={
            EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)
            ],
            EXPENSE_CATEGORY: [
                CallbackQueryHandler(
                    receive_category, pattern=r"^expense:category:[a-z]+$"
                )
            ],
            EXPENSE_DESCRIPTION: [
                CallbackQueryHandler(skip_description, pattern=r"^expense:skip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description),
            ],
        },
        fallbacks=[
            CommandHandler("start", restart_from_conversation),
            CommandHandler("menu", menu_from_conversation),
            CommandHandler("cancel", cancel_expense),
            CallbackQueryHandler(menu_from_conversation, pattern=r"^menu:main$"),
            CallbackQueryHandler(cancel_expense, pattern=r"^expense:cancel$"),
        ],
        allow_reentry=True,
        name="add_expense",
        persistent=True,
    )

    application.add_handler(expense_conversation)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_main_menu))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("stats", show_monthly_stats))
    application.add_handler(CommandHandler("recent", show_recent_expenses))
    application.add_handler(CommandHandler("undo", show_undo_expense))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern=r"^menu:main$"))
    application.add_handler(
        CallbackQueryHandler(show_recent_expenses, pattern=r"^menu:recent$")
    )
    application.add_handler(
        CallbackQueryHandler(show_monthly_stats, pattern=r"^menu:stats$")
    )
    application.add_handler(
        CallbackQueryHandler(show_undo_expense, pattern=r"^menu:undo$")
    )
    application.add_handler(
        CallbackQueryHandler(
            confirm_delete_expense,
            pattern=r"^expense:delete:\d+$",
        )
    )
    application.add_handler(CallbackQueryHandler(show_help, pattern=r"^menu:help$"))
    logger.info("Telegram bot application initialized")
    return application
