from decimal import Decimal

from sqlalchemy import select
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
