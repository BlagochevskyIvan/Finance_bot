from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import User as TelegramUser

from db.models import Expense, User


async def upsert_user(session: AsyncSession, telegram_user: TelegramUser) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_user.id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_user.id)
        session.add(user)

    user.username = telegram_user.username
    user.first_name = telegram_user.first_name
    user.last_name = telegram_user.last_name
    await session.flush()
    return user


async def add_expense(
    session: AsyncSession,
    *,
    user: User,
    amount: Decimal,
    category: str,
    description: str | None,
) -> Expense:
    expense = Expense(
        user=user,
        amount=amount,
        category=category,
        description=description,
    )
    session.add(expense)
    await session.flush()
    return expense


async def get_recent_expenses(
    session: AsyncSession, user_id: int, *, limit: int = 10
) -> list[Expense]:
    result = await session.scalars(
        select(Expense)
        .where(Expense.user_id == user_id)
        .order_by(Expense.spent_at.desc(), Expense.id.desc())
        .limit(limit)
    )
    return list(result)


async def get_current_month_totals(
    session: AsyncSession, user_id: int
) -> list[tuple[str, str, Decimal]]:
    month_start = func.date_trunc("month", func.now())
    result = await session.execute(
        select(
            Expense.category,
            Expense.currency,
            func.sum(Expense.amount).label("total"),
        )
        .where(
            Expense.user_id == user_id,
            Expense.spent_at >= month_start,
        )
        .group_by(Expense.category, Expense.currency)
        .order_by(func.sum(Expense.amount).desc(), Expense.category)
    )
    return [
        (category, currency, total)
        for category, currency, total in result.all()
    ]
