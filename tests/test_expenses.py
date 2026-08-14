import unittest
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from config.states import EXPENSE_AMOUNT
from db.models import Base, Expense
from handlers.common import (
    format_expense,
    format_monthly_stats,
    format_recent_expenses,
)
from handlers.bot_init import BOT_COMMANDS
from handlers.expenses import DRAFT_KEY, parse_amount, start_add_expense


class ParseAmountTests(unittest.TestCase):
    def test_parses_integer_and_decimal_amounts(self) -> None:
        self.assertEqual(parse_amount("350"), Decimal("350.00"))
        self.assertEqual(parse_amount("1 250,5"), Decimal("1250.50"))

    def test_rejects_invalid_amounts(self) -> None:
        for value in ("", "text", "0", "-10", "NaN", "Infinity"):
            with self.subTest(value=value):
                self.assertIsNone(parse_amount(value))


class AddExpenseCommandTests(unittest.IsolatedAsyncioTestCase):
    async def test_starts_expense_flow_from_command_message(self) -> None:
        message = SimpleNamespace(reply_text=AsyncMock())
        update = SimpleNamespace(callback_query=None, effective_message=message)
        context = SimpleNamespace(user_data={DRAFT_KEY: {"stale": True}})

        state = await start_add_expense(update, context)

        self.assertEqual(state, EXPENSE_AMOUNT)
        self.assertEqual(context.user_data[DRAFT_KEY], {})
        message.reply_text.assert_awaited_once()


class BotCommandMenuTests(unittest.TestCase):
    def test_publishes_every_documented_command(self) -> None:
        commands = {command.command for command in BOT_COMMANDS}

        self.assertEqual(
            commands,
            {"start", "add", "menu", "help", "recent", "stats", "undo", "cancel"},
        )


class ExpenseModelTests(unittest.TestCase):
    def test_expense_table_is_related_to_users(self) -> None:
        self.assertIn("expenses", Base.metadata.tables)
        foreign_keys = {key.target_fullname for key in Expense.__table__.foreign_keys}
        self.assertEqual(foreign_keys, {"users.id"})


class MonthlyStatsTests(unittest.TestCase):
    def test_formats_category_and_currency_totals(self) -> None:
        totals = [
            ("🍔 Еда", "RUB", Decimal("1200.50")),
            ("🚕 Транспорт", "RUB", Decimal("300.00")),
        ]

        text = format_monthly_stats(totals)

        self.assertIn("🍔 Еда: <b>1200.50 RUB</b>", text)
        self.assertIn("🚕 Транспорт: <b>300.00 RUB</b>", text)
        self.assertTrue(text.endswith("1500.50 RUB"))

    def test_formats_empty_month(self) -> None:
        self.assertEqual(
            format_monthly_stats([]),
            "В этом месяце расходов пока нет.",
        )


class ExpenseFormattingTests(unittest.TestCase):
    def test_formats_expense_and_escapes_user_text(self) -> None:
        expense = Expense(
            amount=Decimal("499.90"),
            currency="RUB",
            category="Дом & ремонт",
            description="Лампа <белая>",
            spent_at=datetime(2026, 8, 10, tzinfo=UTC),
        )

        text = format_expense(expense)

        self.assertIn("10.08.2026 · Дом &amp; ремонт", text)
        self.assertIn("<b>499.90 RUB</b>", text)
        self.assertIn("Лампа &lt;белая&gt;", text)

    def test_formats_recent_expenses_and_escapes_user_text(self) -> None:
        expense = Expense(
            amount=Decimal("150.00"),
            currency="RUB",
            category="Еда & напитки",
            description="Кофе <латте>",
            spent_at=datetime(2026, 8, 11, tzinfo=UTC),
        )

        text = format_recent_expenses([expense])

        self.assertIn("11.08.2026 · Еда &amp; напитки", text)
        self.assertIn("Кофе &lt;латте&gt;", text)

    def test_formats_empty_recent_expenses(self) -> None:
        self.assertEqual(
            format_recent_expenses([]),
            "У вас пока нет расходов. Добавьте первый.",
        )


if __name__ == "__main__":
    unittest.main()
