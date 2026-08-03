import unittest
from decimal import Decimal

from db.models import Base, Expense
from handlers.expenses import parse_amount


class ParseAmountTests(unittest.TestCase):
    def test_parses_integer_and_decimal_amounts(self) -> None:
        self.assertEqual(parse_amount("350"), Decimal("350.00"))
        self.assertEqual(parse_amount("1 250,5"), Decimal("1250.50"))

    def test_rejects_invalid_amounts(self) -> None:
        for value in ("", "text", "0", "-10", "NaN", "Infinity"):
            with self.subTest(value=value):
                self.assertIsNone(parse_amount(value))


class ExpenseModelTests(unittest.TestCase):
    def test_expense_table_is_related_to_users(self) -> None:
        self.assertIn("expenses", Base.metadata.tables)
        foreign_keys = {key.target_fullname for key in Expense.__table__.foreign_keys}
        self.assertEqual(foreign_keys, {"users.id"})


if __name__ == "__main__":
    unittest.main()
